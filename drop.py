from app import create_app, db  # Import create_app and db from your application
from models.models import Expense, Bill, Income, ExpenseCategory  # Import all models

# Create the Flask app instance
app = create_app()

# Use the application context to perform database operations
with app.app_context():
    # Drop all tables
    db.drop_all()
    print("All tables have been dropped.")