from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for
from models.models import db, Expense, Bill, Income
from sqlalchemy import text
from calendar import monthrange

bp = Blueprint('expenses', __name__, url_prefix='/expenses')

@bp.route("/", methods=["GET", "POST"])
def manage_expenses():
    # Get the current month and previous month
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)
    start_of_previous_month = start_of_month - timedelta(days=1)
    start_of_previous_month = datetime(start_of_previous_month.year, start_of_previous_month.month, 1)
    # End of the current month
    end_of_month = datetime(now.year, now.month, monthrange(now.year, now.month)[1])

    # Query to get only relevant bills and incomes from the current and previous month
    try:
        with db.engine.connect() as conn:
            query = """
            SELECT *
            FROM budget_view
            WHERE expected_date >= :start_date AND expected_date < :end_date
            """
            result = conn.execute(
                text(query),
                {
                    'start_date': start_of_previous_month,
                    'end_date': end_of_month + timedelta(days=1) 
                }
            )
            budget_view_data = [dict(row._mapping) for row in result]
    except Exception as e:
        return f"Error occurred while querying budget_view: {e}", 500

    if request.method == "POST":
        try:
            name = request.form.get("expense-description")
            amount = float(request.form.get("expense-amount", 0))
            date_str = request.form.get("expense-date")
            cleared = 'cleared-checkbox' in request.form  # Check if the checkbox is selected
            bill_id = request.form.get("bill-id")  # Get the bill ID from the form

            if not name or not amount or not date_str:
                return "All fields are required.", 400

            date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Create a new expense, setting linked_id to the selected bill_id if available
            new_expense = Expense(
                description=name,
                amount=amount,
                date=date,
                cleared=cleared,
                linked_id=bill_id if bill_id else None  # Store the bill ID or None if no bill is selected
            )

            db.session.add(new_expense)
            db.session.commit()
        except Exception as e:
            return f"Error occurred: {e}", 500
        return redirect(url_for("expenses.manage_expenses"))

    expenses = Expense.query.all()
    bills = Bill.query.all()
    incomes = Income.query.all()

    # Look up the linked Bill or Income for each expense
    for expense in expenses:
        if expense.linked_id:
            linked_entry = Bill.query.get(expense.linked_id) or Income.query.get(expense.linked_id)
            expense.linked_name = linked_entry.name if linked_entry else None
        else:
            expense.linked_name = None

    return render_template(
        "expenses.html",
        expenses=expenses,
        budget_view_data=budget_view_data,
        bills=bills,
        incomes=incomes
    )


@bp.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    # Find the expense by its ID
    expense_to_delete = Expense.query.get(expense_id)

    if expense_to_delete:
        db.session.delete(expense_to_delete)
        db.session.commit()
        return redirect(url_for('expenses.manage_expenses'))
    else:
        return 'Expense not found', 404

