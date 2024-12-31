from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from models.models import Bill, db, BillCategory
from datetime import datetime
import logging
from sqlalchemy.exc import IntegrityError
from db_setup import refresh_budget_tables

# Set up logging to a file for easier debugging
logging.basicConfig(filename='app.log', level=logging.DEBUG)

bp = Blueprint('bills', __name__, url_prefix='/bills')

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

        # Fetch the category ID from BillCategory or create a new category if not found
        category = BillCategory.query.filter_by(name=bill_category).first()

        if not category:
            # If the category does not exist, create it
            category = BillCategory(name=bill_category)
            db.session.add(category)
            try:
                db.session.commit()  # Commit the new category to the database
            except IntegrityError:
                db.session.rollback()  # Rollback if there is any error (e.g., duplicate entry)
                return 'Category could not be added', 400

        # Create and add the new bill
        new_bill = Bill(
            name=bill_name,
            amount= float(bill_amount)*-1,
            due_day=int(bill_due_day),
            category_id=category.id  # Link to the category ID
        )
        db.session.add(new_bill)
        db.session.commit()

        # Redirect back to the bills page after the form submission
        return redirect(url_for('bills.manage_bills'))

    # Fetch all bills and categories
    now = datetime.now()
    year = now.year
    month = now.month
    bills = Bill.query.all()  # Fetch all bills
    categories = BillCategory.query.all()  # Fetch all categories

    refresh_budget_tables()  # Call the stored procedure to refresh the budget table

    return render_template("bills.html", bills=bills, categories=categories, year=year, month=month, now=now)


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

    # Check if the category exists or create it
    category = BillCategory.query.filter_by(name=bill_category).first()
    if not category:
        category = BillCategory(name=bill_category)
        db.session.add(category)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': 'Category could not be added'}), 400

    # Update the bill's details
    bill_to_edit.name = bill_name
    bill_to_edit.amount = float(bill_amount)
    bill_to_edit.due_day = int(bill_due_day)
    bill_to_edit.category_id = category.id  # Link to the new or existing category

    refresh_budget_tables()  # Call the stored procedure to refresh the budget table

    db.session.commit()

    # Redirect back to the bills page after editing the bill
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

    refresh_budget_tables()  # Call the stored procedure to refresh the budget table
    # Redirect back to the bills page after deleting the bill
    
    return redirect(url_for('bills.manage_bills'))
