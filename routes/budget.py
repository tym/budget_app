from flask import Blueprint, render_template, jsonify, request
from sqlalchemy.sql import text
import logging
logging.basicConfig(level=logging.INFO)
from models.models import db
from datetime import datetime

bp = Blueprint('budget', __name__, url_prefix='/budget')

# Route to render the budget page
@bp.route("/", methods=["GET"])
def budget_home():
    # Get the current year and month
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Get the year and month from the query parameters, if available
    year = request.args.get('year', type=int, default=current_year)
    month = request.args.get('month', type=int, default=current_month)

    # Query the materialized view to get budget entries
    try:
        with db.engine.connect() as conn:
            query = """
            SELECT 
                bd.entry_type,
                bd.name as description,
                bd.expected_date,
                bd.expected_amount,
                e.amount AS actual_amount,
                e.date AS actual_date,  -- Fetching actual date from expenses table
                bd.cleared
            FROM budget_view bd
            LEFT JOIN expenses e ON bd.expense_id = e.id
            WHERE EXTRACT(YEAR FROM bd.expected_date) = :year
            AND EXTRACT(MONTH FROM bd.expected_date) = :month
            AND (bd.expense_id IS NULL OR e.id IS NOT NULL)  -- Only fetch actual date if there's a linked expense
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
        # Convert string date to datetime object
        date = datetime.strptime(date_str, '%Y-%m-%d')

        # Define the WHERE clause for cleared based on the passed parameter
        cleared_condition = ""
        if cleared == "0":  # Means uncleared
            cleared_condition = "AND (bd.cleared IS NULL OR bd.cleared = 'No')"
        elif cleared == "1":  # Means cleared
            cleared_condition = "AND bd.cleared = 'Yes'"

        with db.engine.connect() as conn:
            query = f"""
                SELECT 
                    bd.entry_type,
                    bd.name,
                    bd.expected_date,
                    bd.expected_amount,
                    e.amount AS actual_amount,
                    e.date AS actual_date,
                    bd.cleared
                FROM budget_view bd
                LEFT JOIN expenses e ON bd.expense_id = e.id
                WHERE 
                    DATE(bd.expected_date) = :date
                    AND bd.entry_type = :entry_type
                    {cleared_condition}  -- Dynamically adds cleared filter
                ORDER BY bd.expected_date;
            """

            result = conn.execute(text(query), {'date': date, 'entry_type': entry_type})
            details = [dict(row._mapping) for row in result]

            # Process data for expected and actual values
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
        return jsonify([])  # Return an empty list on error



# Route to get day data
@bp.route('/get-day-data', methods=["GET"])
def get_day_data():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    day_data = {}
    previous_actual_balance = 0.0
    previous_expected_balance = 0.0  # New tracking for expected balance

    try:
        with db.engine.connect() as conn:
            query = """
                SELECT 
                    DATE(expected_date) AS day,
                    entry_type,
                    SUM(CASE WHEN cleared = 'Yes' THEN expected_amount ELSE 0 END) AS actual_amount,
                    SUM(CASE WHEN cleared IS NULL OR cleared != 'Yes' THEN expected_amount ELSE 0 END) AS expected_amount
                FROM budget_view
                WHERE EXTRACT(YEAR FROM expected_date) = :year
                  AND EXTRACT(MONTH FROM expected_date) = :month
                GROUP BY DATE(expected_date), entry_type
                ORDER BY DATE(expected_date), entry_type;
            """
            result = conn.execute(text(query), {'year': year, 'month': month})
            rows = [dict(row._mapping) for row in result]
            
            rows.sort(key=lambda x: x['day'])

            for row in rows:
                day = row['day'].strftime('%Y-%m-%d')

                if day not in day_data:
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

                if row['entry_type'] == 'Income':
                    day_data[day]['actual_income'] += row['actual_amount']
                    day_data[day]['expected_income'] += row['expected_amount']
                elif row['entry_type'] == 'Bill':
                    day_data[day]['actual_bills'] += row['actual_amount']
                    day_data[day]['expected_bills'] += row['expected_amount']
                elif row['entry_type'] == 'Expense':
                    day_data[day]['actual_expenses'] += row['actual_amount']
                    day_data[day]['expected_expenses'] += row['expected_amount']

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
                


        return jsonify(day_data)

    except Exception as e:
        logging.error(f"Error generating day data: {e}")
        return jsonify({})
