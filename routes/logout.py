from flask_login import logout_user, redirect, url_for
from flask import Blueprint

bp = Blueprint('logout', __name__, url_prefix='/logout')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))
