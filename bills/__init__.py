from flask import Blueprint, render_template, request, redirect, url_for
from models.models import db, Bill  # Import db and Bill model from models

bp = Blueprint('bills', __name__, url_prefix='/bills')

@bp.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Handling form submission
        name = request.form["bill-name"]
        amount = float(request.form["bill-amount"])
        due_day = int(request.form["bill-due_day"])
        category = request.form["bill-category"]

        new_bill = Bill(name=name, amount=amount, due_day=due_day, category=category)
        db.session.add(new_bill)
        db.session.commit()

        # Redirect to the same page after submission to avoid resubmission on refresh
        return redirect(url_for('bills.index'))

    # Query all bills from the database for the GET request
    bills = Bill.query.all()
    return render_template('bills.html', bills=bills)
