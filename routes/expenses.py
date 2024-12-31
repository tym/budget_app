from flask import Blueprint, render_template, request, redirect, url_for
from models.models import db, Expense, Bill, Income, ExpenseCategory  # Import ExpenseCategory model
from datetime import datetime, timedelta
from sqlalchemy import text

bp = Blueprint('expenses', __name__, url_prefix='/expenses')
@bp.route("/", methods=["GET", "POST"])
def manage_expenses():
    try:
        if request.method == "POST":
            expense_id = request.form.get("expense-id")
            description = request.form.get("expense-description")
            amount = float(request.form.get("expense-amount", 0))
            date_str = request.form.get("expense-date")
            category_name = request.form.get("expense-category")
            cleared = 'cleared-checkbox' in request.form
            new_category = request.form.get("new-category")
            bill_id = request.form.get("bill-id")
            income_id = request.form.get("income-id")

            # Default category handling (if custom category is not entered)
            if new_category:
                category_name = new_category

            # Ensure category exists in the database (if using foreign key)
            category = None
            if category_name:
                category = ExpenseCategory.query.filter_by(name=category_name).first()
                if not category and new_category:  # Create a new category if not found
                    category = ExpenseCategory(name=new_category)
                    db.session.add(category)
                    db.session.flush()  # Flush to get the ID without committing

            # Convert date string to date object
            if not date_str:
                return "Date is required.", 400
            date = datetime.strptime(date_str, "%Y-%m-%d").date()

            if expense_id:  # Edit existing expense
                expense = Expense.query.get(expense_id)
                if not expense:
                    return "Expense not found.", 404
                expense.description = description
                expense.amount = amount
                expense.date = date
                expense.category = category.name if category else None
                expense.cleared = cleared
                expense.linked_id = bill_id if bill_id else income_id
                db.session.commit()
            else:  # Create new expense
                if not description or not amount or not date_str:
                    return "All fields are required.", 400

                new_expense = Expense(
                    description=description,
                    amount=amount,
                    date=date,
                    category=category.name if category else None,
                    cleared=cleared,
                    linked_id=bill_id if bill_id else income_id
                )

                # Call the stored procedure to refresh the table
                refresh_sql = "CALL public.refresh_budget_tables();"
                db.session.execute(text(refresh_sql))

                db.session.add(new_expense)
                db.session.commit()



            return redirect(url_for('expenses.manage_expenses'))

        # Handle GET request: Fetch existing expenses
        expenses = Expense.query.all()
        categories = ExpenseCategory.query.all()
        bills = Bill.query.all()
        incomes = Income.query.all()
        return render_template(
            "expenses.html",
            expenses=expenses,
            categories=categories,
            bills=bills,
            incomes=incomes
        )
    except Exception as e:
        return f"Error occurred: {e}", 500


@bp.route("/edit/<string:expense_id>", methods=["GET"])
def edit_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return "Expense not found.", 404

    bills = Bill.query.all()
    incomes = Income.query.all()
    categories = ExpenseCategory.query.all()  # Fetch categories for editing

    # Call the stored procedure to refresh the table
    refresh_sql = "CALL public.refresh_budget_tables();"
    db.session.execute(text(refresh_sql))

    # Prepopulate the form with the expense data for editing
    return render_template(
        "edit_expense.html",
        expense=expense,
        bills=bills,
        incomes=incomes,
        categories=categories  # Pass categories to frontend
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
