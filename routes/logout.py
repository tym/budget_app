from flask_login import logout_user
from flask import Blueprint, redirect, url_for, request

bp = Blueprint('logout', __name__, url_prefix='/logout', static_folder='static', template_folder='templates')

@bp.route('/', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        logout_user()
        return redirect(url_for('auth.login'))
    return redirect(url_for('auth.login'))  # Optional: handle GET if needed
