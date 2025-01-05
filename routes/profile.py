from flask_login import current_user
from flask import Blueprint
from flask_login import login_required

bp = Blueprint('profile', __name__, url_prefix='/profile')

@bp.route('/profile')
@login_required
def profile():
    return f"Welcome, {current_user.username}!"
