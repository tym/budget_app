from flask import Blueprint, render_template, jsonify, request
from sqlalchemy.sql import text
import logging
from models.models import db
from datetime import datetime

logging.basicConfig(level=logging.INFO)

bp = Blueprint('budget', __name__, url_prefix='/budget')

# Route to render the budget page
@bp.route("/", methods=["GET"])
def budget_home():
    current_year = datetime.now().year
    current_month = datetime.now().month

    year = request.args.get('year', type=int, default=current_year)
    month = request.args.get('month', type=int, default=current_month)

    try:
        with db.engine.connect() as conn:
            query = """
            SELECT 
                bd.entry_id AS entry_id,            
                bd.entry_type,
                bd.description AS description,
                bd.expected_date,
                bd.expected_amount,
                bd.actual_amount,
                bd.actual_date,
                bd.cleared,
                bd.not_expected
            FROM budget_table bd
            WHERE (
                (EXTRACT(YEAR FROM bd.expected_date) = :year AND EXTRACT(MONTH FROM bd.expected_date) = :month)
                OR 
                (EXTRACT(YEAR FROM bd.actual_date) = :year AND EXTRACT(MONTH FROM bd.actual_date) = :month)
            )
            ORDER BY bd.expected_date;
            """
            result = conn.execute(text(query), {'year': year, 'month': month})
            budget_entries = [dict(row._mapping) for row in result]

        return render_template("budget.html", year=year, month=month, budget_entries=budget_entries)

    except Exception as e:
        logging.error(f"Error fetching budget entries: {e}")
        return render_template("budget.html", year=year, month=month, budget_entries=[])

@bp.route('/get-details', methods=["GET"])
def get_details():
    date_str = request.args.get('date', type=str)
    entry_type = request.args.get('entry_type', type=str)
    cleared = request.args.get('cleared', type=str)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        cleared_condition = ""
        if cleared == "0":  # Means uncleared
            cleared_condition = "AND (bd.cleared IS NULL OR bd.cleared = 'No')"
        elif cleared == "1":  # Means cleared
            cleared_condition = "AND bd.cleared = 'Yes'"

        with db.engine.connect() as conn:
            query = f"""
            SELECT 
                bd.entry_type,
                bd.description,
                bd.expected_date,
                bd.expected_amount,
                bd.actual_amount,
                bd.actual_date,
                bd.cleared
            FROM budget_table bd
            WHERE 
                (YEAR(bd.expected_date) = :year AND MONTH(bd.expected_date) = :month) 
                OR (YEAR(bd.actual_date) = :year AND MONTH(bd.actual_date) = :month)
                AND bd.entry_type = :entry_type
                {cleared_condition}
            ORDER BY bd.expected_date;

            """

            result = conn.execute(text(query), {'date': date, 'entry_type': entry_type})
            details = [dict(row._mapping) for row in result]

            for entry in details:
                if entry['cleared'] == 'Yes':
                    entry['amount'] = entry['actual_amount']
                    entry['date'] = entry['actual_date']
                else:
                    entry['amount'] = entry['expected_amount']
                    entry['date'] = entry['expected_date']

        return jsonify(details)

    except Exception as e:
        logging.error(f"Error fetching details for {date_str}: {e}")
        return jsonify([])

@bp.route('/edit-budget-entry', methods=['POST'])
def edit_budget_entry():
    data = request.json
    entry_id = data.get('entry_id')
    actual_amount = data.get('actual_amount')
    actual_date = data.get('actual_date')
    cleared = data.get('cleared')
    not_expected = data.get('not_expected')

    try:
        # Debugging: Log the received data
        logging.info(f"Received data: {data}")

        # Ensure None for empty fields to pass NULL to the database
        actual_amount = None if actual_amount == '' else actual_amount
        actual_date = None if actual_date == '' else actual_date
        cleared = None if cleared == '' else cleared
        not_expected = None if not_expected == '' else not_expected

        # Update the `expenses` table if the `cleared` field is not None
        if cleared is not None and entry_id.startswith('Expense'):
            update_expense_sql = """
            UPDATE expenses
            SET cleared = :cleared
            WHERE expense_id = :expense_id
            """
            db.session.execute(text(update_expense_sql), {
                'cleared': cleared, 
                'expense_id': entry_id.replace('Expense', '')
            })

        # Update the `budget_table`
        update_budget_sql = """
        UPDATE budget_table
        SET actual_amount = :actual_amount,
            actual_date = :actual_date,
            not_expected = :not_expected
        WHERE entry_id = :entry_id
        """
        result = db.session.execute(text(update_budget_sql), {
            'actual_amount': actual_amount,
            'actual_date': actual_date,
            'not_expected': not_expected,
            'entry_id': entry_id
        })

        # Debugging: Log the number of rows affected
        logging.info(f"Rows affected in budget_table: {result.rowcount}")

        # Call the stored procedure to refresh the table
        refresh_sql = "CALL public.refresh_budget_tables();"
        db.session.execute(text(refresh_sql))

        # Commit the changes
        db.session.flush()
        db.session.commit()
        logging.info("Changes committed successfully.")

        return jsonify({'status': 'success', 'message': 'Budget entry updated successfully'}), 200

    except Exception as e:
        # Rollback on error
        db.session.rollback()
        logging.error(f"Error occurred: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500




@bp.route('/get-day-data', methods=["GET"])
def get_day_data():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    day_data = {}
    previous_actual_balance = 0.0
    previous_expected_balance = 0.0

    try:
        with db.engine.connect() as conn:
            query = """
            SELECT 
                DATE(expected_date) AS day,
                entry_type,
                SUM(CASE WHEN not_expected IS FALSE AND cleared = 'Yes' THEN expected_amount ELSE 0 END) AS actual_amount,
                SUM(CASE WHEN not_expected IS FALSE AND (cleared IS NULL OR cleared != 'Yes') THEN expected_amount ELSE 0 END) AS expected_amount
            FROM budget_table
            WHERE (
                (EXTRACT(YEAR FROM expected_date) = :year AND EXTRACT(MONTH FROM expected_date) = :month)
                OR 
                (EXTRACT(YEAR FROM actual_date) = :year AND EXTRACT(MONTH FROM actual_date) = :month)
            )
            GROUP BY DATE(expected_date), entry_type
            ORDER BY DATE(expected_date), entry_type;
            """
            result = conn.execute(text(query), {'year': year, 'month': month})
            rows = [dict(row._mapping) for row in result]
            logging.info(f"Rows returned: {rows}")
            logging.info(f"month: {month}, year: {year}")
            logging.info(f"Initial day_data: {day_data}")

            rows.sort(key=lambda x: x['day'])

            for row in rows:
                day = row['day'].strftime('%Y-%m-%d')  # Convert to string
                logging.info(f"Converted day to string: {day}")
                logging.info(f"Checking day: {day} in day_data keys: {list(day_data.keys())}")

                # If day is not in day_data, add it with initialized values
                if day not in day_data:
                    logging.info(f"Day {day} not found in day_data. Adding it.")
                    day_data[day] = {
                        'actual_income': 0.0,
                        'actual_bills': 0.0,
                        'actual_expenses': 0.0,
                        'actual_balance': previous_actual_balance,
                        'expected_income': 0.0,
                        'expected_bills': 0.0,
                        'expected_expenses': 0.0,
                        'expected_balance': previous_expected_balance,
                    }

                # Log the current entry's amounts before updating
                logging.info(f"Date: {row['day']} | Entry Type: {row['entry_type']} | Actual Amount: {row['actual_amount']} | Expected Amount: {row['expected_amount']}")

                # Process the row based on its entry type
                if row['entry_type'] == 'income':
                    actual_value = float(row['actual_amount']) if row['actual_amount'] is not None else 0.0
                    expected_value = float(row['expected_amount']) if row['expected_amount'] is not None else 0.0
                    
                    logging.info(f"Before Update - Day: {day} | actual_income: {day_data[day]['actual_income']} | expected_income: {day_data[day]['expected_income']}")
                    day_data[day]['actual_income'] += actual_value
                    day_data[day]['expected_income'] += expected_value
                    logging.info(f"After Update - Day: {day} | actual_income: {day_data[day]['actual_income']} | expected_income: {day_data[day]['expected_income']}")

                elif row['entry_type'] == 'bill':
                    actual_value = float(row['actual_amount']) if row['actual_amount'] is not None else 0.0
                    expected_value = float(row['expected_amount']) if row['expected_amount'] is not None else 0.0
                    
                    logging.info(f"Before Update - Day: {day} | actual_bills: {day_data[day]['actual_bills']} | expected_bills: {day_data[day]['expected_bills']}")
                    day_data[day]['actual_bills'] += actual_value
                    day_data[day]['expected_bills'] += expected_value
                    logging.info(f"After Update - Day: {day} | actual_bills: {day_data[day]['actual_bills']} | expected_bills: {day_data[day]['expected_bills']}")

                elif row['entry_type'] == 'expense':
                    actual_value = float(row['actual_amount']) if row['actual_amount'] is not None else 0.0
                    expected_value = float(row['expected_amount']) if row['expected_amount'] is not None else 0.0
                    
                    logging.info(f"Before Update - Day: {day} | actual_expenses: {day_data[day]['actual_expenses']} | expected_expenses: {day_data[day]['expected_expenses']}")
                    day_data[day]['actual_expenses'] += actual_value
                    day_data[day]['expected_expenses'] += expected_value
                    logging.info(f"After Update - Day: {day} | actual_expenses: {day_data[day]['actual_expenses']} | expected_expenses: {day_data[day]['expected_expenses']}")

                # Update the actual and expected balances based on new values
                day_data[day]['actual_balance'] = (
                    previous_actual_balance +
                    day_data[day]['actual_income'] - 
                    day_data[day]['actual_bills'] - 
                    day_data[day]['actual_expenses']
                )
                previous_actual_balance = day_data[day]['actual_balance']

                day_data[day]['expected_balance'] = (
                    previous_expected_balance +
                    day_data[day]['expected_income'] - 
                    day_data[day]['expected_bills'] - 
                    day_data[day]['expected_expenses']
                )
                previous_expected_balance = day_data[day]['expected_balance']

            logging.info(f"Final day_data: {day_data}")

            logging.debug(f"Rows returned: {rows}")
            logging.debug(f"month: {month}, year: {year}")
            logging.debug(f"Initial day_data: {day_data}")

        return jsonify(day_data)

    except Exception as e:
        logging.error(f"Error fetching day data: {e}")
        return jsonify({})