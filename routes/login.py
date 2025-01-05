from flask import render_template, redirect, url_for, request, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash
from models.models import User

# Define the Blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.profile'))  # Redirect if user is already logged in

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):  # Assuming check_password is implemented
            login_user(user)
            return redirect(url_for('auth.profile'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))