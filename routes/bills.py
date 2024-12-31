from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from models.models import Bill, db
from datetime import datetime
import logging

# Set up logging to a file for easier debugging
logging.basicConfig(filename='app.log', level=logging.DEBUG)

bp = Blueprint('bills', __name__, url_prefix='/bills')

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


@bp.route("/", methods=['GET', 'POST'])
def manage_bills():
    if request.method == 'POST':
        # Handle form submission for creating a new bill
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
        return redirect(url_for('bills.manage_bills'))

    now = datetime.now()
    year = now.year
    month = now.month
    bills = Bill.query.all()  # Fetch all bills

    call_refresh_budget_table()  # Call the stored procedure to refresh the budget table

    return render_template("bills.html", bills=bills, year=year, month=month, now=now)

@bp.route("/edit", methods=['POST'])
def edit_bill():
    bill_id = request.form.get('bill-id')
    bill_name = request.form.get('bill-name')
    bill_amount = request.form.get('bill-amount')
    bill_due_day = request.form.get('bill-due_day')
    bill_category = request.form.get('bill-category')

    # Find the bill by its ID
    bill_to_edit = Bill.query.get(bill_id)

    if not bill_to_edit:
        return jsonify({'status': 'error', 'message': 'Bill not found'}), 404

    # Update the bill's details
    bill_to_edit.name = bill_name
    bill_to_edit.amount = float(bill_amount)
    bill_to_edit.due_day = int(bill_due_day)
    bill_to_edit.category = bill_category

    call_refresh_budget_table()  # Call the stored procedure to refresh the budget table

    db.session.commit()

    return redirect(url_for('bills.manage_bills'))


@bp.route("/delete/<string:bill_id>", methods=['POST'])
def delete_bill(bill_id):
    # Log the received bill_id for debugging
    current_app.logger.debug(f"Delete request received for bill_id: {bill_id}")

    # Find the bill by its ID
    bill_to_delete = Bill.query.get(bill_id)

    if not bill_to_delete:
        current_app.logger.error(f"Bill with id {bill_id} not found.")
        return jsonify({'status': 'error', 'message': 'Bill not found'}), 404

    db.session.delete(bill_to_delete)
    db.session.commit()

    current_app.logger.info(f"Bill with id {bill_id} deleted successfully.")

    call_refresh_budget_table()  # Call the stored procedure to refresh the budget table
    return redirect(url_for('bills.manage_bills'))