# Stage 1A review records and execution

## Run the local gate

Use the repository's Python 3.13 environment. From the repository root, install the pinned requirements and run the same entry point for every view.

```sh
.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.review_gate
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.review_gate --section held_pairs
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.review_gate --section approved_comparisons
PYTHONPATH=src .venv/bin/python -m mia_capital_intelligence.review_gate --project CA176A
```

All views run through source validation, candidate generation, review validation and the SQL eligibility relation. Exit code 0 means the inputs passed technical validation. Held pairs are a valid result. Exit code 1 identifies failed source acquisition/loading or invalid review inputs and yields no approved comparisons. A project filter applies after evaluation and retains the global validation result.

The program reads local inputs and prints deterministic JSON to stdout. It supplies no user SQL interface or persistent analytical database. Each execution builds and closes an in-memory DuckDB connection. Source observations retain raw values and evidence, while approved comparisons contain only eligible metric values and approval provenance. Stage 1B is responsible for any future change calculations after scope review and authorization.

## Version-controlled input

The production review bundle is `data/review_dispositions.json`, validated against `schemas/review_dispositions.schema.json`, contract version 1.0. The initial evidence and decisions arrays are empty. This explicitly invokes default-held treatment for every candidate, with reviewer and decision timestamp unassigned. Approval names, timestamps and evidence must come from an actual reviewer.

To supply a real decision, first inspect both original rows through the project view and the [human review packet](HUMAN_REVIEW_PACKET.md). Copy the exact candidate ID and source references from the current report. Prepare a local JSON bundle, validate it with `--reviews path/to/reviews.json`, inspect the result, and commit the reviewed input separately under the project workflow. Record changes in Git so superseded decisions remain available in history. Keep one active decision per candidate and globally unique decision and evidence IDs. Multiple approved metrics belong to that single decision. Repeated or conflicting records are technical errors.

Source references encode matter ID, full document checksum, exhibit, PDF position and physical data-row ordinal. Candidate IDs hash the ordered earlier/later references. A different source version creates different references and invalidates old decisions. The source loader verifies PDF bytes, page boundaries and all 222 ordered ID/amount controls before returning observations.

## Evidence and decision fields

Each decision requires contract version, decision ID, candidate ID, both source references, outcome, rationale, approved metrics, reviewer, decision timestamp, evidence IDs and a specific follow-up question. Outcomes follow the existing contract, `held`, `comparable` and `excluded`. Excluded represents a human rejection or determination of non-comparability. Held drafts may use null reviewer and timestamp. Comparable and excluded decisions require a named reviewer and a valid timezone-aware timestamp. A named held decision also needs a timestamp.

Each supporting evidence record requires an evidence ID, candidate ID, category, applicable metric or null, both original source references, verification status, verifier, verification timestamp, statement and citation. Required approval categories are `original_records`, `project_identity`, `scope`, `financial_metric`, `estimate_basis` and `reporting_period`. Each must be explicitly verified with an attributed verifier and timestamp no later than the decision. Unverified evidence keeps verifier and timestamp null and provides no affirmative confirmation.

Common identity, original-row, scope and period evidence may apply to all named approved metrics using null for its metric. Financial-metric and estimate-basis evidence must name the particular metric. Every metric approved in a comparable decision needs all six dimensions and a usable verified observation on each side. References must bind exactly the current pair. The schema declares the existing dictionary's total estimated cost and current approved budget measures, while the real Stage 1A source set contains total estimated cost only. Budget observations appear exclusively in synthetic tests of metric isolation.

The software checks structure, attribution fields, source lineage, evidence coverage and query eligibility. Human review supplies the substantive assertions that scope and estimate basis are equivalent. Reviewer identity is an attributed input claim, with authentication outside this local pilot. A verified JSON assertion should cite a concrete basis for its conclusion.

Any technical error invalidates the whole submitted bundle's eligibility relation for that run. This conservative policy includes schema errors, unknown or stale references, duplicate decisions, incomplete approval evidence, unverified evidence, and approved metrics with missing values. Valid source observations and candidate matches remain inspectable when the review bundle is invalid. Invalid source inputs retain their raw observations and errors and yield no analytical joins.

## Safe unassigned draft example

This is a held draft for the real CA176A pair, with no human decision attributed. Its exact reference fields were checked against the current source rows. Keep the production bundle empty until a reviewer supplies an intended record.

```json
{
  "schema_version": "1.0",
  "evidence": [],
  "decisions": [{
    "contract_version": "1.0",
    "decision_id": "ca176a-unassigned-draft",
    "candidate_id": "pair-3b558a641c7255e8aaeb41a23f6da02142b763752c5b417457c1a817747b34b2",
    "earlier_source_ref": "260526:eaf845f4fb746a69940f38fe4655d27b56ab42effdbf9cfdd1dbc746a0fba878:B:11:42",
    "later_source_ref": "261402:84751b451da8b7d5e06cad6b1c24c870e563de5669c5f07325033c446bbaeb2a:B:12:41",
    "outcome": "held",
    "rationale": "The later Ph2 label and later-only CA176B leave scope and estimate basis unconfirmed.",
    "approved_metrics": [],
    "reviewer": null,
    "decided_at": null,
    "evidence_ids": [],
    "follow_up_question": "Which earlier seating scope belongs to CA176A and CA176B, and is the estimate basis equivalent?"
  }]
}
```

Positive examples are explicitly synthetic in `tests/test_comparability.py`, in its `approval` helper. The test creates verified evidence for all six dimensions and a synthetic named reviewer. Use it to understand the shape and executable conditions, then supply real evidence and an actual human decision for production use.

## SQL and debugging

`sql/candidates.sql` performs a same-exhibit full outer join on exact project IDs. Before that join, the source validator checks row and project-key uniqueness, expected source versions, exhibit boundaries and strictly ordered nonoverlapping memo periods. One-sided rows are returned as report-presence observations with their source reference.

`comparability.evaluate_gate` validates the complete review bundle. Only after every technical condition succeeds does it insert metric-specific grants into `eligible_metrics`. `sql/approved_metrics.sql` joins that relation to both source metric cells, restricts the outcome to comparable, and requires usable amounts with matching units. Decimal values use DuckDB DECIMAL(18,2) and JSON decimal strings. No other public query path constructs an approved cross-report result.

In PyCharm choose `.venv/bin/python`, set the repository root as working directory, and add `src` to PYTHONPATH. A Python module configuration targeting `mia_capital_intelligence.review_gate` with `--project CA176A` shows the real held path. Break at `evaluate_gate` before eligible-metric insertion and inspect the empty grants and structured reasons. For the positive path, debug `test_approval_is_metric_specific_and_decimal_exact` with pytest. Compare the approved cost row with the blocked budget metric and inspect the SQL result after `approved_metrics.sql` executes.
