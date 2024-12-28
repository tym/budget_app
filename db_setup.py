from sqlalchemy import text
from models.models import db

def setup_budget_view_and_triggers():
    # SQL to drop the materialized view if it exists
    drop_materialized_view_sql = """
    DROP MATERIALIZED VIEW IF EXISTS budget_view CASCADE;
    """

    # SQL to create the materialized view with an id column
    create_materialized_view_sql = """
    CREATE MATERIALIZED VIEW budget_view AS
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
            NULL::INTEGER AS expense_id
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
            NULL::INTEGER AS expense_id
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
            NULL::INTEGER AS expense_id
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
            e.id AS expense_id
        FROM 
            expenses e
    )
    SELECT 
        ROW_NUMBER() OVER (ORDER BY expected_date) AS id,
        entry_type,
        income_id,
        bill_id,
        expense_id,
        name,
        expected_amount,
        expected_date,
        cleared
    FROM (
        SELECT 
            related_id, name, expected_amount, entry_type, first_period_date, expected_date, income_id, bill_id, expense_id
        FROM date_series
        UNION ALL
        SELECT 
            related_id, name, expected_amount, entry_type, first_period_date, expected_date, income_id, bill_id, expense_id
        FROM bills_series
        UNION ALL
        SELECT 
            related_id, name, expected_amount, entry_type, first_period_date, expected_date, income_id, bill_id, expense_id
        FROM expenses_series
    ) AS combined_data
    LEFT JOIN 
        expenses e ON (combined_data.entry_type = 'Expense' AND combined_data.expense_id = e.id)
    ORDER BY 
        expected_date;

    """

    # SQL to create a unique index on the id column
    create_unique_index_sql = """
    CREATE UNIQUE INDEX budget_view_id_idx ON budget_view (id);
    """

    try:
        with db.engine.connect() as conn:
            # Drop the materialized view if it exists
            conn.execute(text(drop_materialized_view_sql))
            print("Materialized view dropped successfully.")
            
            # Create the materialized view with the id column
            conn.execute(text(create_materialized_view_sql))
            print("Materialized view created successfully.")
            
            # Create the unique index on the id column
            conn.execute(text(create_unique_index_sql))
            print("Unique index created successfully.")
            
            conn.commit()
    except Exception as e:
        print(f"Error setting up materialized view: {e}")
