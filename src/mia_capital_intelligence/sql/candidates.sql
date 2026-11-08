-- Identity matching creates candidates. Approval is evaluated separately.
SELECT
    COALESCE(earlier.project_id, later.project_id) AS project_id,
    earlier.source_ref AS earlier_ref,
    later.source_ref AS later_ref
FROM (SELECT * FROM source_rows WHERE matter_id = ?) AS earlier
FULL OUTER JOIN (SELECT * FROM source_rows WHERE matter_id = ?) AS later
    ON earlier.project_id = later.project_id
    AND earlier.exhibit = later.exhibit
ORDER BY project_id;
