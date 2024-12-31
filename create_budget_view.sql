from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from models.models import db
import logging

def setup_budget_table():
    """Set up the budget_table by creating it from the budget_view."""
    try:
        # Check if the table already exists
        check_table_query = """
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_name = 'budget_table'
        );
        """
        result = db.session.execute(text(check_table_query)).fetchone()
        table_exists = result[0] if result else False
        
        if not table_exists:
            # Table doesn't exist, create it
            create_query = """
            CREATE TABLE budget_table AS
            WITH first_period AS (
                SELECT 
                    i.id AS income_id,
                    i.name,
                    i.amount AS expected_amount,
                    i.start_date,
                    i.frequency,
                    i.day_of_week,
                    i.start_date + 
                        CASE 
                            WHEN EXTRACT(DOW FROM i.start_date) <= 
                                CASE 
                                    WHEN i.day_of_week = 'sunday' THEN 0
                                    WHEN i.day_of_week = 'monday' THEN 1
                                    WHEN i.day_of_week = 'tuesday' THEN 2
                                    WHEN i.day_of_week = 'wednesday' THEN 3
                                    WHEN i.day_of_week = 'thursday' THEN 4
                                    WHEN i.day_of_week = 'friday' THEN 5
                                    WHEN i.day_of_week = 'saturday' THEN 6
                                END 
                            THEN 
                                ((CASE 
                                    WHEN i.day_of_week = 'sunday' THEN 0
                                    WHEN i.day_of_week = 'monday' THEN 1
                                    WHEN i.day_of_week = 'tuesday' THEN 2
                                    WHEN i.day_of_week = 'wednesday' THEN 3
                                    WHEN i.day_of_week = 'thursday' THEN 4
                                    WHEN i.day_of_week = 'friday' THEN 5
                                    WHEN i.day_of_week = 'saturday' THEN 6
                                END - EXTRACT(DOW FROM i.start_date)) * INTERVAL '1 day')
                            ELSE 
                                ((7 + CASE 
                                    WHEN i.day_of_week = 'sunday' THEN 0
                                    WHEN i.day_of_week = 'monday' THEN 1
                                    WHEN i.day_of_week = 'tuesday' THEN 2
                                    WHEN i.day_of_week = 'wednesday' THEN 3
                                    WHEN i.day_of_week = 'thursday' THEN 4
                                    WHEN i.day_of_week = 'friday' THEN 5
                                    WHEN i.day_of_week = 'saturday' THEN 6
                                END - EXTRACT(DOW FROM i.start_date)) * INTERVAL '1 day')
                        END AS first_period_date,
                    'Income' AS entry_type,
                    i.id AS related_id,
                    NULL::INTEGER AS bill_id,
                    NULL::INTEGER AS expense_id,
                    NULL::BOOLEAN AS not_expected,  -- Set to NULL for incomes (no cleared field)
                    NULL::NUMERIC AS actual_amount,  -- New column for actual amount
                    NULL::DATE AS actual_date  -- New column for actual date
                FROM 
                    incomes i
            ),
            date_series AS (
                SELECT 
                    f.related_id,
                    f.name,
                    f.expected_amount,
                    f.entry_type,
                    f.first_period_date,
                    f.first_period_date + 
                        (n * CASE 
                            WHEN f.entry_type = 'Income' THEN 
                                CASE 
                                    WHEN f.frequency = 'weekly' THEN 7
                                    WHEN f.frequency = 'biweekly' THEN 14
                                    WHEN f.frequency = 'monthly' THEN 30
                                    ELSE 0
                                END * INTERVAL '1 day'
                            ELSE INTERVAL '0 day'
                        END) AS expected_date,
                    f.related_id AS income_id,
                    NULL::INTEGER AS bill_id,
                    NULL::INTEGER AS expense_id,
                    f.not_expected,  -- Include from first_period
                    NULL::NUMERIC AS actual_amount,  -- New column for actual amount
                    NULL::DATE AS actual_date  -- New column for actual date
                FROM
                    first_period f
                CROSS JOIN 
                    GENERATE_SERIES(0, 1000) AS n
            ),
            bills_series AS (
                SELECT 
                    b.id AS related_id,
                    b.name,
                    b.amount AS expected_amount,
                    'Bill' AS entry_type,
                    DATE_TRUNC('month', CURRENT_DATE) AS first_period_date,
                    DATE_TRUNC('month', CURRENT_DATE) + (b.due_day - 1) * INTERVAL '1 day' AS expected_date,
                    b.id AS bill_id,
                    NULL::INTEGER AS income_id,
                    NULL::INTEGER AS expense_id,
                    NULL::BOOLEAN AS not_expected,  -- Set to NULL for bills (no cleared field)
                    NULL::NUMERIC AS actual_amount,  -- New column for actual amount
                    NULL::DATE AS actual_date  -- New column for actual date
                FROM 
                    bills b
            ),
            expenses_series AS (
                SELECT 
                    e.id AS related_id,
                    e.description AS name,
                    e.amount AS expected_amount,
                    'Expense' AS entry_type,
                    e.date AS first_period_date,
                    e.date AS expected_date,
                    NULL::INTEGER AS bill_id,
                    NULL::INTEGER AS income_id,
                    e.id AS expense_id,
                    CASE 
                        WHEN e.cleared IS NULL THEN TRUE  -- Mark as not expected if cleared is NULL
                        ELSE FALSE 
                    END AS not_expected,  -- Set based on cleared field for expenses
                    e.amount AS actual_amount,  -- New column for actual amount
                    e.date AS actual_date  -- New column for actual date
                FROM 
                    expenses e
            )
            SELECT 
                ROW_NUMBER() OVER (ORDER BY expected_date) AS entry_id,
                entry_type,
                income_id,
                bill_id,
                expense_id,
                name,
                expected_amount,
                expected_date,
                cleared,
                not_expected,  -- Include the not_expected field in the final output
                actual_amount,  -- Include actual_amount column
                actual_date  -- Include actual_date column
            FROM (
                SELECT 
                    related_id, name, expected_amount, entry_type, first_period_date, expected_date, income_id, bill_id, expense_id, not_expected, actual_amount, actual_date
                FROM date_series
                UNION ALL
                SELECT 
                    related_id, name, expected_amount, entry_type, first_period_date, expected_date, income_id, bill_id, expense_id, not_expected, actual_amount, actual_date
                FROM bills_series
                UNION ALL
                SELECT 
                    related_id, name, expected_amount, entry_type, first_period_date, expected_date, income_id, bill_id, expense_id, not_expected, actual_amount, actual_date
                FROM expenses_series
            ) AS combined_data
            LEFT JOIN 
                expenses e ON (combined_data.entry_type = 'Expense' AND combined_data.expense_id = e.id)
            ORDER BY 
                expected_date;
            """
            # Execute the query to create the table
            db.session.execute(text(create_query))
            db.session.commit()
        
        else:
            # If the table exists, just log a message
            logging.info("Table 'budget_table' already exists, no creation needed.")
            
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error creating or checking budget_table: {e}")
        raise

def update_budget_entry(entry_id, actual_amount, actual_date, not_expected):
    """Update a specific entry in the budget_table."""
    try:
        # Default values if not set
        if actual_date == '':
            actual_date = None  # Set to None if not provided
        if not_expected is None:
            not_expected = False  # Default to False if not provided

        # Log the parameters
        logging.info(f"Updating entry {entry_id}: actual_amount={actual_amount}, actual_date={actual_date}, cleared={cleared}, not_expected={not_expected}")

        # Your update query
        update_query = """
        UPDATE budget_table
        SET actual_amount = :actual_amount,
            actual_date = :actual_date,
            not_expected = :not_expected
        WHERE entry_id = :entry_id
        """

        # Execute the query and pass parameters
        result = db.session.execute(text(update_query), {
            'actual_amount': actual_amount, 
            'actual_date': actual_date,  
            'not_expected': not_expected, 
            'entry_id': entry_id
        })

        # Commit the transaction
        db.session.commit()

        # Log the number of rows affected
        logging.info(f"Rows affected by budget update: {result.rowcount}")
        
        if result.rowcount == 0:
            logging.warning(f"No rows updated for entry_id={entry_id}.")
        else:
            logging.info("Changes committed to the database.")

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error updating budget_table: {e}")
        raise

def refresh_budget_table():
    """Refresh the budget_table by truncating and repopulating it."""
    try:
        # Truncate the existing table to remove old data
        truncate_query = "TRUNCATE TABLE budget_table;"
        db.session.execute(text(truncate_query))
        
        # Repopulate the table by calling the stored procedure
        refresh_sql = "SELECT public.refresh_budget_table();"
        db.session.execute(text(refresh_sql))
        
        db.session.commit()
        logging.info("Budget table refreshed successfully.")

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"Error occurred while refreshing budget_table: {e}")
        raise
