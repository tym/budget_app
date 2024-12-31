from flask import Blueprint, render_template, request, redirect, url_for
from models.models import db, Expense, Bill, Income
from datetime import datetime, timedelta

bp = Blueprint('expenses', __name__, url_prefix='/expenses')

@bp.route("/", methods=["GET", "POST"])
def manage_expenses():
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

    if request.method == "POST":
        try:
            # Handle adding a new expense or updating an existing one
            expense_id = request.form.get("expense-id")
            if expense_id:  # Edit existing expense
                expense = Expense.query.get(expense_id)
                if not expense:
                    return "Expense not found.", 404
                expense.description = request.form.get("expense-description")
                expense.amount = float(request.form.get("expense-amount", 0))
                expense.date = datetime.strptime(request.form.get("expense-date"), "%Y-%m-%d").date()
                expense.category = request.form.get("expense-category")
                expense.cleared = 'cleared-checkbox' in request.form
                expense.linked_id = request.form.get("bill-id") or None
                db.session.commit()
            else:  # Add new expense
                name = request.form.get("expense-description")
                amount = float(request.form.get("expense-amount", 0))
                date_str = request.form.get("expense-date")
                cleared = 'cleared-checkbox' in request.form
                bill_id = request.form.get("bill-id")

                if not name or not amount or not date_str:
                    return "All fields are required.", 400

                date = datetime.strptime(date_str, "%Y-%m-%d").date()

                new_expense = Expense(
                    description=name,
                    amount=amount,
                    date=date,
                    cleared=cleared,
                    linked_id=bill_id if bill_id else None
                )

                db.session.add(new_expense)
                db.session.commit()
        except Exception as e:
            return f"Error occurred: {e}", 500

        return redirect(url_for("expenses.manage_expenses"))

    return render_template(
        "expenses.html",
        expenses=expenses,
        bills_and_incomes=bills + incomes  # Combined list for selection
    )

@bp.route("/edit/<string:expense_id>", methods=["GET"])
def edit_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return "Expense not found.", 404

    bills = Bill.query.all()
    incomes = Income.query.all()

    # Prepopulate the form with the expense data for editing
    return render_template(
        "edit_expense.html",
        expense=expense,
        bills=bills,
        incomes=incomes
    )

@bp.route("/delete/<string:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    expense_to_delete = Expense.query.get(expense_id)
    if expense_to_delete:
        db.session.delete(expense_to_delete)
        db.session.commit()
        return redirect(url_for('expenses.manage_expenses'))
    else:
        return 'Expense not found', 404
