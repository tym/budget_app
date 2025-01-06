from flask import Flask, redirect, url_for, request
from flask.cli import with_appcontext
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user 
import click
from datetime import datetime
from models.models import db, User
from routes.budget import bp as budget_bp
from routes.income import bp as income_bp
from routes.bills import bp as bills_bp
from routes.expenses import bp as expenses_bp
from routes.login import bp as auth_bp
from routes.profile import bp as profile_bp
from routes.settings import bp as settings_bp
from routes.logout import bp as logout_bp
from routes.signup import bp as signup_bp 
from db_setup import setup_budget_table, refresh_budget_tables
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def create_app():
    app = Flask(__name__)
    
    # Set a secret key for session management
    app.config['SECRET_KEY'] = 'your-very-secret-key'  # Make sure to use a strong, random secret key

    app.config.from_object("config.Config")  # Load config

    # Login Manager setup
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"  # Redirect unauthorized users to this route
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(budget_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(bills_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(logout_bp)
    app.register_blueprint(signup_bp)

    # Before each request, ensure the user is logged in
    @app.before_request
    def ensure_logged_in():
        # Skip static file requests
        if request.endpoint and request.endpoint.startswith('static'):
            return None  # Do nothing for static file requests

        # Check if the endpoint exists and whether it starts with "auth" or "signup"
        if request.endpoint and not (request.endpoint.startswith("auth") or request.endpoint.startswith("signup")):
            # If the user is not authenticated, redirect to the signup page
            if not current_user.is_authenticated:
                return redirect(url_for("signup.signup"))

        
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


    @app.route("/")
    @login_required
    def index():
        return redirect("/budget")

    @app.context_processor
    def inject_now():
        return {"now": datetime.now()}

    # Flask CLI commands
    @app.cli.command("setup_db")
    @with_appcontext
    def setup_db_command():
        click.echo("Setting up the budget table...")
        setup_budget_table()
        refresh_budget_tables()
        click.echo("Database setup complete.")

    @app.cli.command("refresh_budget")
    @with_appcontext
    def refresh_budget_command():
        click.echo("Refreshing the budget table...")
        refresh_budget_tables()
        click.echo("Budget table refreshed successfully.")

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        setup_budget_table()
        refresh_budget_tables()
        print("Database setup and refresh complete.")
    app.run(debug=True)
