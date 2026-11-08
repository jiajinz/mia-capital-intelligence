-- The application supplies fixed SQL fragments and binds every user filter value.
-- Grain is one source record. This query creates no historical change metric.
SELECT
    source_ref, project_id, project_name, description_raw, airport_code, airport_name,
    matter_id, period_start, period_end, estimate_usd, pdf_page
FROM directory_records
WHERE {where}
ORDER BY {order_by};
