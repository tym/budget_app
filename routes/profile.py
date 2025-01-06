from flask_login import current_user
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from flask_login import login_required

bp = Blueprint('profile', __name__, url_prefix='/profile')

@bp.route('/')
@login_required
def profile():
    # Render the profile template and pass the username as context
    return render_template('profile.html', username=current_user.username)
