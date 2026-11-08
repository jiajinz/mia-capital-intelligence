-- Only validated, metric-specific review grants can enter this relation.
-- Stage 1A returns source values and provenance. Change calculation belongs to Stage 1B.
SELECT
    grant_row.candidate_id,
    grant_row.project_id,
    grant_row.metric,
    grant_row.decision_id,
    grant_row.reviewer,
    grant_row.earlier_ref,
    grant_row.later_ref,
    earlier.amount AS earlier_value,
    later.amount AS later_value,
    earlier.unit
FROM eligible_metrics AS grant_row
JOIN source_amounts AS earlier
    ON earlier.source_ref = grant_row.earlier_ref AND earlier.metric = grant_row.metric
JOIN source_amounts AS later
    ON later.source_ref = grant_row.later_ref AND later.metric = grant_row.metric
WHERE grant_row.outcome = 'comparable'
    AND earlier.amount IS NOT NULL AND later.amount IS NOT NULL
    AND earlier.unit = later.unit
ORDER BY grant_row.project_id, grant_row.metric, grant_row.candidate_id;
