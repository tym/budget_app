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
        # Log that the refresh process has started
        logging.info("Starting refresh of the budget_table...")

        # Get a connection from the engine
        with db.session.begin():  # Start a transaction context
            # Truncate the budget_table
            db.session.execute(text("TRUNCATE TABLE budget_table;"))
            logging.info("budget_table truncated successfully.")

            # Repopulate the budget_table based on actual table columns
            db.session.execute(text("""
                INSERT INTO budget_table (entry_id, entry_type, description, expected_date, actual_date, expected_amount, actual_amount, cleared, not_expected)
                SELECT 
                    -- Generating unique entry_id for each row based on month, year, and specific ID
                    CONCAT(LPAD(EXTRACT(MONTH FROM CURRENT_DATE)::TEXT, 2, '0'),
                           EXTRACT(YEAR FROM CURRENT_DATE)::TEXT,
                           CASE
                               WHEN type = 'bill' THEN 'Bill' || bill_id
                               WHEN type = 'expense' THEN 'Expense' || expense_id
                               WHEN type = 'income' THEN 'Income' || income_id
                           END) AS entry_id,
                    type AS entry_type,
                    description,
                    expected_date,
                    actual_date,
                    expected_amount,
                    actual_amount,
                    cleared,
                    not_expected
                FROM (
                    -- Income logic
                    SELECT 'income' AS type, 
                           name AS description, 
                           generated_date AS expected_date, 
                           NULL AS actual_date,
                           i.amount AS expected_amount, 
                           NULL AS actual_amount, 
                           FALSE AS cleared, 
                           FALSE AS not_expected,
                           i.income_id,
                           NULL AS bill_id,
                           NULL AS expense_id
                    FROM incomes i,
                         generate_series(
                            GREATEST(i.start_date, date_trunc('month', CURRENT_DATE)),
                            date_trunc('month', CURRENT_DATE) + interval '1 month' - interval '1 day',
                            CASE 
                                WHEN i.frequency = 'weekly' THEN interval '1 week'
                                WHEN i.frequency = 'biweekly' THEN interval '2 weeks'
                                WHEN i.frequency = 'monthly' THEN interval '1 month'
                            END
                         ) AS generated_date
                    WHERE extract(month FROM generated_date) = extract(month FROM CURRENT_DATE)
                      AND extract(year FROM generated_date) = extract(year FROM CURRENT_DATE)

                    UNION ALL

                    -- Expense logic
                    SELECT 'expense' AS type, 
                           e.description, 
                           e.date AS expected_date, 
                           e.date AS actual_date, 
                           e.amount AS expected_amount, 
                           e.amount AS actual_amount, 
                           e.cleared, 
                           FALSE AS not_expected,
                           NULL AS income_id,
                           NULL AS bill_id,
                           e.expense_id
                    FROM expenses e
                    WHERE extract(month FROM e.date) = extract(month FROM CURRENT_DATE)
                          AND extract(year FROM e.date) = extract(year FROM CURRENT_DATE)

                    UNION ALL

                    -- Bill logic
                    SELECT 'bill' AS type, 
                           b.name AS description, 
                           make_date(extract(year FROM CURRENT_DATE)::INT, extract(month FROM CURRENT_DATE)::INT, b.due_day) AS expected_date,
                           NULL AS actual_date, 
                           b.amount AS expected_amount, 
                           NULL AS actual_amount, 
                           FALSE AS cleared, 
                           FALSE AS not_expected,
                           NULL AS income_id,
                           b.bill_id,
                           NULL AS expense_id
                    FROM bills b
                    WHERE b.due_day BETWEEN 1 AND 31
                ) combined_data
                ON CONFLICT (entry_id) DO NOTHING;  -- Skip if the entry_id already exists
            """))
            logging.info("budget_table populated successfully with new data.")

    except Exception as e:
        # Log any errors that occur
        logging.error(f"Error refreshing budget_table: {str(e)}")
        print(f"Error refreshing budget_table: {e}")

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
