
-- Create the 'incomes' table
CREATE TABLE IF NOT EXISTS incomes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    amount FLOAT NOT NULL,
    frequency VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Create the 'bills' table
CREATE TABLE IF NOT EXISTS bills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    amount FLOAT NOT NULL,
    due_day INTEGER NOT NULL,
    category VARCHAR(255) NULL
);

-- Create the 'expenses' table
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    description VARCHAR(80) NOT NULL,
    amount FLOAT NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    category VARCHAR(50) NULL,
    cleared BOOLEAN DEFAULT FALSE,
    bill_id INTEGER REFERENCES bills(id) ON DELETE SET NULL,
    income_id INTEGER REFERENCES incomes(id) ON DELETE SET NULL
);


DROP VIEW IF EXISTS budget_view;

CREATE VIEW budget_view AS
SELECT
    ROW_NUMBER() OVER (ORDER BY i.start_date) AS id,  -- Add a unique ID column
    'income' AS type,
    i.name,
    i.amount AS expected_amount,
    COALESCE(SUM(e.amount), 0) AS actual_amount,
    i.start_date AS expected_date,
    CASE WHEN COALESCE(SUM(e.amount), 0) >= i.amount THEN true ELSE false END AS cleared,
    false AS not_expected,
    TO_CHAR(i.start_date, 'YYYY') AS year,
    TO_CHAR(i.start_date, 'MM') AS month
FROM
    incomes i
LEFT JOIN
    expenses e ON e.description = i.name AND e.cleared = true
WHERE
    TO_CHAR(i.start_date, 'MM') = TO_CHAR(CURRENT_DATE, 'MM')
    AND TO_CHAR(i.start_date, 'YYYY') = TO_CHAR(CURRENT_DATE, 'YYYY')
GROUP BY
    i.name, i.amount, i.start_date

UNION ALL

SELECT
    ROW_NUMBER() OVER (ORDER BY b.due_day) AS id,  -- Add a unique ID column
    'bill' AS type,
    b.name,
    b.amount AS expected_amount,
    COALESCE(SUM(e.amount), 0) AS actual_amount,
    (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 day' * b.due_day) AS expected_date,
    CASE WHEN COALESCE(SUM(e.amount), 0) >= b.amount THEN true ELSE false END AS cleared,
    true AS not_expected,
    TO_CHAR(CURRENT_DATE, 'YYYY') AS year,
    TO_CHAR(CURRENT_DATE, 'MM') AS month
FROM
    bills b
LEFT JOIN
    expenses e ON e.description = b.name AND e.cleared = true
WHERE
    (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 day' * b.due_day)::DATE = CURRENT_DATE
    AND TO_CHAR(CURRENT_DATE, 'YYYY') = TO_CHAR(CURRENT_DATE, 'YYYY')
GROUP BY
    b.name, b.amount, b.due_day;
