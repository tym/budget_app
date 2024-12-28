from flask import Flask, redirect
from flask.cli import with_appcontext
from flask_migrate import Migrate
import click
from datetime import datetime
from models.models import db
from routes.budget import bp as budget_bp
from routes.income import bp as income_bp
from routes.bills import bp as bills_bp
from routes.expenses import bp as expenses_bp
from db_setup import setup_budget_view_and_triggers

print.log("test")
def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(budget_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(bills_bp)
    app.register_blueprint(expenses_bp)

    @app.route("/")
    def index():
        return redirect("/budget")

    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    @app.cli.command("setup_db")
    @with_appcontext
    def setup_db_command():
        click.echo("Setting up database views and triggers...")
        setup_budget_view_and_triggers()
        click.echo("Database setup complete.")

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        setup_budget_view_and_triggers()  # Set up database views and triggers here
        print("Database schema refreshed.")
    app.run(debug=True)
