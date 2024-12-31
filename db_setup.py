from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from models.models import db
import logging

logging.basicConfig(level=logging.INFO)

def setup_budget_table():
    try:
        # Check if the table exists in the database
        table_exists = db.session.execute(
            text(""" 
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'budget_table'
                );
            """)
        ).scalar()  # .scalar() fetches the single value from the query result

        if table_exists:
            # If the table exists, drop it
            db.session.execute(text("DROP TABLE IF EXISTS budget_table;"))
            db.session.commit()  # Commit the transaction to drop the table
            logging.info("budget_table dropped successfully.")
        
        # Recreate the table with the updated column names
        db.session.execute(text("""
            CREATE TABLE budget_table (
                entry_id text PRIMARY KEY,
                entry_type VARCHAR(10) NOT NULL, -- 'income', 'bill', or 'expense'
                description TEXT NOT NULL,
                expected_date DATE NOT NULL,
                actual_date DATE,
                expected_amount NUMERIC NOT NULL,
                actual_amount NUMERIC,
                cleared BOOLEAN DEFAULT FALSE,
                not_expected BOOLEAN DEFAULT FALSE
            );
        """))
        db.session.commit()  # Commit the transaction to create the table
        logging.info("budget_table created successfully.")

        # Call the refresh_budget_table stored procedure to populate/refresh the data
        refresh_budget_tables()  # Now call the refresh function

        return "Budget table setup completed successfully."

    except Exception as e:
        # Handle any exceptions
        db.session.rollback()  # Rollback in case of error
        logging.error(f"Error setting up budget table: {str(e)}")
        return f"Error setting up budget table: {str(e)}"


def refresh_budget_tables():
    """
    Refreshes the `budget_table` by truncating and repopulating it based on updated data in
    the `incomes`, `expenses`, and `bills` tables.
    """
    try:
        # Execute the stored procedure
        with db.engine.connect() as connection:
            connection.execute(text("CALL refresh_budget_tables();"))
            connection.commit()
        print("Stored procedure executed successfully.")
    except Exception as e:
        print(f"Error occurred while calling stored procedure: {e}")
        
def update_budget_entry(entry_id, actual_amount, actual_date, not_expected):
    """Update an existing budget entry."""
    try:
        # Ensure actual_date is handled properly
        if not actual_date:
            actual_date = None

        # Log the operation
        logging.info(f"Updating entry {entry_id} with actual_amount={actual_amount}, actual_date={actual_date}, not_expected={not_expected}")

        # Update the existing entry
        update_query = """
        UPDATE budget_table
        SET actual_amount = :actual_amount,
            actual_date = :actual_date,
            not_expected = :not_expected
        WHERE entry_id = :entry_id;
        """

        result = db.session.execute(text(update_query), {
            'entry_id': entry_id,
            'actual_amount': actual_amount,
            'actual_date': actual_date,
            'not_expected': not_expected
        })

        # Commit changes
        db.session.commit()

        if result.rowcount == 0:
            logging.warning(f"No rows updated for entry_id={entry_id}. Please check the data.")
        else:
            logging.info("Entry updated successfully.")

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error updating budget entry: {e}")
        raise
