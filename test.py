from app import create_app  # Adjust import as necessary
from models.models import reflect_budget_view

app = create_app()

with app.app_context():  # Ensure this block runs within the app context
    try:
        budget_view = reflect_budget_view(app)

        if budget_view is not None:
            print("Reflection successful! The 'budget_view' table was found.")
            print(f"Columns: {[column.name for column in budget_view.columns]}")
        else:
            print("Error: 'budget_view' was not reflected correctly.")
    except Exception as e:
        print(f"An error occurred: {e}")
