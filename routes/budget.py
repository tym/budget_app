from flask import Blueprint, jsonify, request
from sqlalchemy.sql import text
import logging
from app import db

bp = Blueprint('budget', __name__, url_prefix='/budget')

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

# Add additional routes as needed below
