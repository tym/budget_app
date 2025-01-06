from flask import render_template, redirect, url_for, request, Blueprint
from flask_login import login_user, current_user
from models.models import User

bp = Blueprint("auth", __name__, url_prefix="/auth", static_folder='static', template_folder='templates')

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))  # If already logged in, redirect to the home page

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):  # Ensure check_password is implemented in the User model
            login_user(user)
            next_page = request.args.get("next")  # Get the intended next page or home
            return redirect(next_page or url_for("index"))  # Redirect to next page or home page
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")  # If the request is GET, render the login template
