from flask import Blueprint, render_template, request, redirect, url_for
from models.models import db, Income
from datetime import datetime

bp = Blueprint('income', __name__, url_prefix='/income')

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
            new_income = Income(name=name, amount=amount, frequency=frequency, day_of_week=day_of_week, start_date=start_date)
            db.session.add(new_income)
            db.session.commit()
        except Exception as e:
            return f"Error occurred: {e}", 500

        return redirect(url_for("income.manage_income"))

    incomes = Income.query.all()
    return render_template("income.html", incomes=incomes)

@bp.route("/delete/<int:income_id>", methods=["POST"])
def delete_income(income_id):
    try:
        income_to_delete = Income.query.get(income_id)
        if income_to_delete:
            db.session.delete(income_to_delete)
            db.session.commit()
        else:
            return "Income entry not found.", 404
    except Exception as e:
        return f"Error occurred: {e}", 500

    return redirect(url_for("income.manage_income"))
