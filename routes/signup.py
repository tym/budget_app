from flask import render_template, redirect, url_for, request, Blueprint
from flask_login import login_user, current_user
from models.models import db, User  # Make sure you have your User model and db setup correctly

bp = Blueprint("signup", __name__, url_prefix="/signup")

@bp.route("/", methods=["GET", "POST"])
def signup():
    # Redirect to /budget if the user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('budget.index'))  # Redirect to the budget page if already logged in

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        password_confirmation = request.form["password_confirmation"]

        # Ensure passwords match
        if password != password_confirmation:
            return render_template("signup.html", error="Passwords do not match")

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template("signup.html", error="Username already exists")

        # Create a new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)  # Ensure `set_password` is implemented in the User model
        db.session.add(new_user)
        db.session.commit()

        # Log in the new user
        login_user(new_user)

        return redirect(url_for("/"))  # Redirect to the budget page or another protected route

    return render_template("signup.html")
