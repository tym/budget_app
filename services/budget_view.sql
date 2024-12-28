CREATE VIEW budget_view AS
SELECT
    'income' AS type,
    i.name,
    i.amount AS expected_amount,
    COALESCE(SUM(e.amount), 0) AS actual_amount,
    i.start_date AS expected_date,
    CASE WHEN COALESCE(SUM(e.amount), 0) >= i.amount THEN true ELSE false END AS cleared,
    false AS not_expected
FROM
    income i
LEFT JOIN
    expense e ON e.description = i.name AND e.cleared = true
WHERE
    MONTH(i.start_date) = MONTH(CURRENT_DATE)
    AND YEAR(i.start_date) = YEAR(CURRENT_DATE)
GROUP BY
    i.name, i.amount, i.start_date

UNION ALL

SELECT
    'bill' AS type,
    b.name,
    b.amount AS expected_amount,
    COALESCE(SUM(e.amount), 0) AS actual_amount,
    DATE_FORMAT(CONCAT(YEAR(CURRENT_DATE), '-', MONTH(CURRENT_DATE), '-', b.due_day), '%Y-%m-%d') AS expected_date,
    CASE WHEN COALESCE(SUM(e.amount), 0) >= b.amount THEN true ELSE false END AS cleared,
    true AS not_expected
FROM
    bill b
LEFT JOIN
    expense e ON e.description = b.name AND e.cleared = true
WHERE
    MONTH(CONCAT(YEAR(CURRENT_DATE), '-', MONTH(CURRENT_DATE), '-', b.due_day)) = MONTH(CURRENT_DATE)
    AND YEAR(CONCAT(YEAR(CURRENT_DATE), '-', MONTH(CURRENT_DATE), '-', b.due_day)) = YEAR(CURRENT_DATE)
GROUP BY
    b.name, b.amount, b.due_day;
