from flask import Blueprint, render_template, request, redirect, url_for
from models.models import Bill, Income, Expense, db
from datetime import datetime
from sqlalchemy import extract

bp = Blueprint('bills', __name__, url_prefix='/bills')

@bp.route("/", methods=['GET', 'POST'])
def manage_bills():
    if request.method == 'POST':
        bill_name = request.form.get('bill-name')
        bill_amount = request.form.get('bill-amount')
        bill_due_day = request.form.get('bill-due_day')
        bill_category = request.form.get('bill-category')

        if not bill_name or not bill_amount or not bill_due_day:
            return 'Please fill out all fields', 400

        new_bill = Bill(
            name=bill_name,
            amount=float(bill_amount),
            due_day=int(bill_due_day),
            category=bill_category
        )
        db.session.add(new_bill)
        db.session.commit()

        # Redirect using the blueprint and function name
        return redirect(url_for('bills.manage_bills'))  # Correctly resolves to '/bills/'

    now = datetime.now()
    year = now.year
    month = now.month
    bills = Bill.query.filter(Bill.due_day >= 1, Bill.due_day <= 31).all()

    # Use 'extract' to filter by the month
    income = Income.query.filter(extract('month', Income.start_date) == month).all()
    expenses = Expense.query.filter(extract('month', Expense.date) == month).all()

    day_data = {i: {'expected_income': 0.0, 'expected_expenses': 0.0, 'actual_expenses': 0.0} for i in range(1, 32)}
    for bill in bills:
        if 1 <= bill.due_day <= 31:
            day_data[bill.due_day]['expected_expenses'] += bill.amount
    for income_entry in income:
        if 1 <= income_entry.start_date.day <= 31:
            day_data[income_entry.start_date.day]['expected_income'] += income_entry.amount
    for expense in expenses:
        if 1 <= expense.date.day <= 31:
            day_data[expense.date.day]['actual_expenses'] += expense.amount

    return render_template("bills.html", day_data=day_data, year=year, month=month, now=now, bills=bills)

@bp.route("/delete/<int:bill_id>", methods=['POST'])
def delete_bill(bill_id):
    # Find the bill by its ID
    bill_to_delete = Bill.query.get(bill_id)

    if bill_to_delete:
        db.session.delete(bill_to_delete)
        db.session.commit()
        return redirect(url_for('bills.manage_bills'))
    else:
        return 'Bill not found', 404
    
@bp.route("/update", methods=['POST'])
def update_bill():
    bill_id = request.form.get('bill-id')
    bill_name = request.form.get('bill-name')
    bill_amount = request.form.get('bill-amount')
    bill_due_day = request.form.get('bill-due_day')
    bill_category = request.form.get('bill-category')

    if not bill_name or not bill_amount or not bill_due_day:
        return 'Please fill out all fields', 400

    bill_to_update = Bill.query.get(bill_id)

    if bill_to_update:
        bill_to_update.name = bill_name
        bill_to_update.amount = float(bill_amount)
        bill_to_update.due_day = int(bill_due_day)
        bill_to_update.category = bill_category

        db.session.commit()
        return redirect(url_for('bills.manage_bills'))

    return 'Bill not found', 404
