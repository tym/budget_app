from flask import Blueprint, render_template, jsonify, request
from sqlalchemy.sql import text
import logging
from models.models import db
from datetime import datetime
from db_setup import refresh_budget_tables

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

# Route to get the details of a specific budget entry
@bp.route('/get-details', methods=["GET"])
def get_details():
    date_str = request.args.get('date', type=str)
    entry_type = request.args.get('entry_type', type=str)
    cleared = request.args.get('cleared', type=str)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        year = date.year
        month = date.month

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
                (EXTRACT(YEAR FROM bd.expected_date) = :year AND EXTRACT(MONTH FROM bd.expected_date) = :month) 
                OR (EXTRACT(YEAR FROM bd.actual_date) = :year AND EXTRACT(MONTH FROM bd.actual_date) = :month)
                AND bd.entry_type = :entry_type
                {cleared_condition}
            ORDER BY bd.expected_date;
            """

            result = conn.execute(text(query), {'year': year, 'month': month, 'entry_type': entry_type})
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

# Route to edit a specific budget entry
@bp.route('/edit-budget-entry', methods=['GET', 'POST'])
def edit_budget_entry():
    # Log the Content-Type of the request
    logging.info(f"Content-Type: {request.content_type}")

    # Check if the incoming request is JSON
    if request.is_json:
        data = request.json
        logging.info(f"Received JSON data: {data}")
    else:
        logging.error("Received data is not in JSON format.")
        return jsonify({'status': 'error', 'message': 'Invalid content type'}), 400

    # Now process the data as usual
    entry_id = data.get('entry_id')
    actual_amount = data.get('actual_amount')
    actual_date = data.get('actual_date')
    cleared = data.get('cleared')
    not_expected = data.get('not_expected')
    try:
        # Ensure None for empty fields to pass NULL to the database
        actual_amount = None if actual_amount == '' else actual_amount
        actual_date = None if actual_date == '' else actual_date
        cleared = None if cleared == 'False' else cleared
        not_expected = None if not_expected == 'False' else not_expected

        # Update the `expenses` table if the `cleared` field is not None
        if cleared is not None and entry_id.startswith('Expense'):
            expense_id = entry_id.replace('Expense', '')  # Extract expense_id
            update_expense_sql = """
            UPDATE expenses
            SET cleared = :cleared
            WHERE expense_id = :expense_id
            """
            db.session.execute(text(update_expense_sql), {
                'cleared': cleared,
                'expense_id': expense_id
            })
            logging.info(f"Expense with ID {expense_id} updated with cleared={cleared}.")

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

# Route to get day data
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
                if row['entry_type'] == 'Income':
                    actual_value = float(row['actual_amount']) if row['actual_amount'] is not None else 0.0
                    expected_value = float(row['expected_amount']) if row['expected_amount'] is not None else 0.0
                    
                    logging.info(f"Before Update - Day: {day} | actual_income: {day_data[day]['actual_income']} | expected_income: {day_data[day]['expected_income']}")
                    day_data[day]['actual_income'] += actual_value
                    day_data[day]['expected_income'] += expected_value
                    logging.info(f"After Update - Day: {day} | actual_income: {day_data[day]['actual_income']} | expected_income: {day_data[day]['expected_income']}")

                elif row['entry_type'] == 'Bill':
                    actual_value = float(row['actual_amount']) if row['actual_amount'] is not None else 0.0
                    expected_value = float(row['expected_amount']) if row['expected_amount'] is not None else 0.0
                    
                    logging.info(f"Before Update - Day: {day} | actual_bills: {day_data[day]['actual_bills']} | expected_bills: {day_data[day]['expected_bills']}")
                    day_data[day]['actual_bills'] += actual_value
                    day_data[day]['expected_bills'] += expected_value
                    logging.info(f"After Update - Day: {day} | actual_bills: {day_data[day]['actual_bills']} | expected_bills: {day_data[day]['expected_bills']}")

                elif row['entry_type'] == 'Expense':
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

        logging.debug(f"Final day_data: {day_data}")

        return jsonify(day_data)

    except Exception as e:
        logging.error(f"Error fetching day data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Route to fetch budget entries
@bp.route('/get-budget-entries', methods=['GET'])
def get_budget_entries():
    # Get the query parameters from the request
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    entry_type = request.args.get('entry_type', type=str)

    # Make sure the parameters are valid
    if not year or not month or not entry_type:
        return jsonify({'error': 'Missing required parameters'}), 400

    try:
        # Connect to the database and fetch the budget entries
        with db.engine.connect() as conn:
            query = """
            SELECT 
                entry_id, entry_type, description, expected_date, expected_amount,
                actual_amount, actual_date, cleared, not_expected
            FROM budget_table
            WHERE EXTRACT(YEAR FROM expected_date) = :year
            AND EXTRACT(MONTH FROM expected_date) = :month
            AND entry_type = :entry_type
            ORDER BY expected_date;
            """
            result = conn.execute(text(query), {'year': year, 'month': month, 'entry_type': entry_type})
            
            # Convert the result to a list of dictionaries
            entries = [dict(row._mapping) for row in result]

        # Return the result as a JSON response
        return jsonify(entries)

    except Exception as e:
        logging.error(f"Error fetching budget entries: {e}")
        return jsonify({'error': 'Failed to fetch budget entries'}), 500