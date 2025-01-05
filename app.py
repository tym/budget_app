from flask import Flask, redirect
from flask.cli import with_appcontext
from flask_migrate import Migrate
import click
from datetime import datetime
from models.models import db, User
from routes.budget import bp as budget_bp
from routes.income import bp as income_bp
from routes.bills import bp as bills_bp
from routes.expenses import bp as expenses_bp
from db_setup import setup_budget_table, refresh_budget_tables  # Correct imports
import logging
from flask_login import LoginManager


# Configure the logging level and format
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more verbose logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # This will print logs to the console
    ]
)
def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')  # Load config from object
    

    login_manager = LoginManager(app)
    login_manager.login_view = 'login' 
    

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(budget_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(bills_bp)
    app.register_blueprint(expenses_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))   
      

    @app.route("/")
    def index():
        return redirect("/budget")

    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    # Flask CLI command to set up the database and trigger refresh
    @app.cli.command("setup_db")
    @with_appcontext
    def setup_db_command():
        click.echo("Setting up the budget table...")
        setup_budget_table()  # Set up the table
        refresh_budget_tables()  # Trigger the refresh immediately after setup
        click.echo("Database setup complete and budget table refreshed.")

    # Flask CLI command to refresh the budget table
    @app.cli.command("refresh_budget")
    @with_appcontext
    def refresh_budget_command():
        click.echo("Refreshing the budget table...")
        refresh_budget_tables()
        click.echo("Budget table refreshed successfully.")
    

    return app


if __name__ == "__main__":

    # Create the app and run it
    app = create_app()
    with app.app_context():
        db.create_all()  # Ensure the database schema is created
        setup_budget_table()  # Initial setup for the budget table
        refresh_budget_tables()  # Trigger refresh right after setup
        print("Database schema, budget table setup, and refresh complete.")
    app.run(debug=True)
    app.config['LOG_LEVEL'] = logging.DEBUG
    app.logger.setLevel(logging.DEBUG)
