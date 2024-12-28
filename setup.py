from db_setup import setup_budget_view_and_triggers
from flask.cli import with_appcontext
import click

@click.command("setup_db")
@with_appcontext
def setup_db_command():
    click.echo("Setting up database views and triggers...")
    setup_budget_view_and_triggers()
    click.echo("Database setup complete.")
