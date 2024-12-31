from flask import Blueprint, render_template, request, redirect, url_for
from models.models import db, Income
from datetime import datetime
from sqlalchemy import text

bp = Blueprint('income', __name__, url_prefix='/income')

# Function to call the stored procedure refresh_budget_table using SQLAlchemy
def call_refresh_budget_table():
    try:
        # Call the stored procedure to refresh the budget table
        db.session.execute(text("CALL refresh_budget_tables();"))
        db.session.commit()  # Commit the transaction to make the changes effective
    except Exception as e:
        # Log the error if something goes wrong
        db.session.rollback()  # Rollback in case of any error
        print(f"Error occurred while calling stored procedure: {e}")

@bp.route("/", methods=["GET", "POST"])
def manage_income():
    if request.method == "POST":
        try:
            name = request.form.get("income-name")
            amount = float(request.form.get("income-amount", 0))
            frequency = request.form.get("income-frequency")
            day_of_week = request.form.get("income-day")
            start_date_str = request.form.get("income-start-date")

            if not name or not amount or not frequency or not day_of_week or not start_date_str:
                return "All fields are required.", 400

            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

            # Add the income entry to the database
            new_income = Income(name=name, amount=amount, frequency=frequency, day_of_week=day_of_week, start_date=start_date)
            db.session.add(new_income)
            db.session.commit()

            # After adding the income, call the stored procedure to refresh the budget table
            call_refresh_budget_table()

        except Exception as e:
            return f"Error occurred: {e}", 500

        return redirect(url_for("income.manage_income"))

    # Fetch all income entries from the database
    incomes = Income.query.all()
    return render_template("income.html", incomes=incomes)

@bp.route("/delete/<string:income_id>", methods=["POST"])
def delete_income(income_id):
    try:
        # Find the income entry to delete
        income_to_delete = Income.query.get(income_id)
        if income_to_delete:
            db.session.delete(income_to_delete)
            db.session.commit()

            # After deleting the income, call the stored procedure to refresh the budget table
            call_refresh_budget_table()
        else:
            return "Income entry not found.", 404
    except Exception as e:
        return f"Error occurred: {e}", 500

    return redirect(url_for("income.manage_income"))

@bp.route("/edit/<string:income_id>", methods=["POST"])
def edit_income(income_id):
    try:
        income = Income.query.get(income_id)
        if not income:
            return "Income entry not found.", 404

        # Get updated data from the form
        income.name = request.form.get("income-name")
        income.amount = float(request.form.get("income-amount", 0))
        income.frequency = request.form.get("income-frequency")
        income.day_of_week = request.form.get("income-day")
        start_date_str = request.form.get("income-start-date")

        if not income.name or not income.amount or not income.frequency or not income.day_of_week or not start_date_str:
            return "All fields are required.", 400

        income.start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

        # Commit changes to the database
        db.session.commit()

        # After editing the income, call the stored procedure to refresh the budget table
        call_refresh_budget_table()

    except Exception as e:
        return f"Error occurred: {e}", 500

    return redirect(url_for("income.manage_income"))