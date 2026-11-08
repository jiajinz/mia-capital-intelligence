"""Business-rule regressions use explicit synthetic decisions and evidence."""

from copy import deepcopy
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from mia_capital_intelligence.comparability import evaluate_gate
from mia_capital_intelligence.comparability_model import (
    AmountObservation, EVIDENCE_CATEGORIES, SourceDocument, SourceRecord, candidate_id,
)
from mia_capital_intelligence.review_gate import select_view, serialize_report

COST = "total_estimated_cost_usd"
BUDGET = "current_approved_budget_usd"


@pytest.fixture
def documents():
    return (
        SourceDocument("earlier", "a" * 64, "https://example.test/earlier", "Synthetic earlier",
                       date(2025, 1, 1), date(2025, 3, 31), date(2025, 4, 1), "synthetic FY", (1,)),
        SourceDocument("later", "b" * 64, "https://example.test/later", "Synthetic later",
                       date(2025, 4, 1), date(2025, 6, 30), date(2025, 7, 1), "synthetic FY", (1,)),
    )


@pytest.fixture
def records(documents):
    return [
        SourceRecord(doc.matter_id, doc.sha256, "B", 1, 1, "SYNTHETIC-1",
                     "Same synthetic description", {
                         COST: AmountObservation(Decimal("100.01"), "100.01", "Total Estimated Cost"),
                         BUDGET: AmountObservation(Decimal("75.11"), "75.11", "Current Approved Budget"),
                     })
        for doc in documents
    ]


def empty_bundle():
    return {"schema_version": "1.0", "evidence": [], "decisions": []}


def approval(records, metrics=(COST,)):
    earlier, later = records
    pair_id = candidate_id(earlier.source_ref, later.source_ref)
    evidence = [
        {
            "evidence_id": f"synthetic-{metric}-{category}", "candidate_id": pair_id,
            "category": category, "metric": metric,
            "source_refs": [earlier.source_ref, later.source_ref],
            "verification_status": "verified", "verified_by": "Synthetic fixture reviewer",
            "verified_at": "2026-01-01T10:00:00Z",
            "statement": "Explicit synthetic confirmation for a controlled unit test",
            "citation": "Synthetic fixture only",
        }
        for metric in metrics for category in EVIDENCE_CATEGORIES
    ]
    return {"schema_version": "1.0", "evidence": evidence, "decisions": [{
        "contract_version": "1.0", "decision_id": "synthetic-decision", "candidate_id": pair_id,
        "earlier_source_ref": earlier.source_ref, "later_source_ref": later.source_ref,
        "outcome": "comparable", "rationale": "Synthetic explicit approval of listed metrics",
        "approved_metrics": list(metrics), "reviewer": "Synthetic fixture reviewer",
        "decided_at": "2026-01-02T10:00:00Z", "evidence_ids": [row["evidence_id"] for row in evidence],
        "follow_up_question": "Which synthetic assumptions support this unit test?",
    }]}


def assert_blocked(report):
    assert report["approved_comparisons"] == []
    assert report["summary"]["approved"] == 0


def test_equal_identity_description_and_values_stay_held(documents, records):
    report = evaluate_gate(documents, records, empty_bundle())
    assert report["summary"]["held"] == 1
    assert report["summary"]["input_valid"]
    assert report["candidates"][0]["default_review_status"] == "held"
    assert report["candidates"][0]["reviewer"] is None
    assert all(state == "unconfirmed" for state in
               report["candidates"][0]["comparability_checks"][COST].values())
    assert_blocked(report)


def test_approval_is_metric_specific_and_decimal_exact(documents, records):
    records[1] = replace(records[1], metrics={
        **records[1].metrics,
        COST: AmountObservation(Decimal("120.02"), "120.02", "Total Estimated Cost"),
    })
    report = evaluate_gate(documents, records, approval(records))
    assert report["validation_errors"] == []
    assert len(report["approved_comparisons"]) == 1
    row = report["approved_comparisons"][0]
    assert row["metric"] == COST
    assert row["earlier_value"] == Decimal("100.01")
    assert row["later_value"] == Decimal("120.02")
    assert report["blocked_comparisons"][0]["metric"] == BUDGET
    assert report["candidates"][0]["comparability_checks"][BUDGET]["scope"] == "unconfirmed"
    assert "delta" not in row
    assert "change" not in row


@pytest.mark.parametrize("outcome", ["held", "excluded"])
def test_held_and_excluded_have_no_comparison_output(documents, records, outcome):
    bundle = approval(records)
    bundle["decisions"][0].update(outcome=outcome, approved_metrics=[])
    report = evaluate_gate(documents, records, bundle)
    assert report["validation_errors"] == []
    assert report["candidates"][0]["review_status"] == outcome
    assert_blocked(report)


def test_unassigned_held_draft_has_no_fabricated_signoff(documents, records):
    bundle = approval(records)
    bundle["decisions"][0].update(outcome="held", approved_metrics=[], reviewer=None, decided_at=None)
    report = evaluate_gate(documents, records, bundle)
    assert report["validation_errors"] == []
    assert report["candidates"][0]["reviewer"] is None
    assert_blocked(report)


@pytest.mark.parametrize("category", EVIDENCE_CATEGORIES)
def test_each_evidence_dimension_is_required(documents, records, category):
    bundle = approval(records)
    next(row for row in bundle["evidence"] if row["category"] == category).update(
        verification_status="unverified", verified_by=None, verified_at=None,
    )
    report = evaluate_gate(documents, records, bundle)
    assert any(error["code"] == "approval_incomplete" for error in report["validation_errors"])
    assert_blocked(report)


@pytest.mark.parametrize(
    ("field", "value"),
    [("outcome", "approved"), ("reviewer", None), ("decided_at", None),
     ("decided_at", "2026-01-02T10:00:00"), ("approved_metrics", []),
     ("approved_metrics", ["all_fields"]), ("contract_version", "0.9")],
)
def test_invalid_review_schema_fails_closed(documents, records, field, value):
    bundle = approval(records)
    bundle["decisions"][0][field] = value
    report = evaluate_gate(documents, records, bundle)
    assert report["summary"]["candidate_pairs"] == report["summary"]["held"] == 1
    assert any(error["code"] == "review_schema" for error in report["validation_errors"])
    assert_blocked(report)


@pytest.mark.parametrize("conflicting", [False, True])
def test_duplicate_and_conflicting_decisions_block_bundle(documents, records, conflicting):
    bundle = approval(records)
    duplicate = deepcopy(bundle["decisions"][0])
    if conflicting:
        duplicate.update(decision_id="synthetic-second", outcome="excluded", approved_metrics=[])
    bundle["decisions"].append(duplicate)
    report = evaluate_gate(documents, records, bundle)
    assert any(error["code"] == "review_duplicate" for error in report["validation_errors"])
    assert_blocked(report)


@pytest.mark.parametrize("mutation", [
    "evidence_ref", "decision_ref", "candidate_ref", "missing_evidence",
    "duplicate_evidence", "future_verification", "generic_financial_metric",
])
def test_invalid_evidence_blocks_comparison(documents, records, mutation):
    bundle = approval(records)
    evidence = bundle["evidence"][0]
    decision = bundle["decisions"][0]
    if mutation == "evidence_ref":
        evidence["source_refs"][0] = "unknown-source"
    elif mutation == "decision_ref":
        decision["earlier_source_ref"] = "unknown-source"
    elif mutation == "candidate_ref":
        decision["candidate_id"] = "unknown-pair"
    elif mutation == "missing_evidence":
        decision["evidence_ids"].append("missing-evidence")
    elif mutation == "duplicate_evidence":
        bundle["evidence"].append(deepcopy(evidence))
    elif mutation == "future_verification":
        evidence["verified_at"] = "2026-01-03T10:00:00Z"
    elif mutation == "generic_financial_metric":
        next(row for row in bundle["evidence"] if row["category"] == "financial_metric")["metric"] = None
    report = evaluate_gate(documents, records, bundle)
    assert report["validation_errors"]
    assert_blocked(report)


def test_changed_checksum_invalidates_dependent_decision(documents, records):
    bundle = approval(records)
    documents = (documents[0], replace(documents[1], sha256="c" * 64))
    records[1] = replace(records[1], document_sha256="c" * 64)
    report = evaluate_gate(documents, records, bundle)
    assert any(error["code"] == "decision_reference" for error in report["validation_errors"])
    assert report["summary"]["held"] == 1
    assert_blocked(report)


@pytest.mark.parametrize("mutation", ["checksum", "exhibit", "page", "duplicate", "period", "reversed"])
def test_invalid_source_lineage_and_cardinality_block_outputs(documents, records, mutation):
    if mutation == "checksum":
        records[1] = replace(records[1], document_sha256="c" * 64)
    elif mutation == "exhibit":
        records[1] = replace(records[1], exhibit="A")
    elif mutation == "page":
        records[1] = replace(records[1], pdf_page=9)
    elif mutation == "duplicate":
        records.append(records[0])
    elif mutation == "period":
        documents = (documents[0], replace(documents[1], period_start=documents[0].period_end))
    elif mutation == "reversed":
        documents = tuple(reversed(documents))
    report = evaluate_gate(documents, records, empty_bundle())
    assert report["validation_errors"]
    assert len(report["source_observations"]) == len(records)
    assert_blocked(report)


@pytest.mark.parametrize("amount", [None, Decimal("NaN"), Decimal("1E+100"), Decimal("1.001")])
def test_unusable_approved_amount_blocks_comparison(documents, records, amount):
    bundle = approval(records)
    records[1] = replace(records[1], metrics={
        COST: replace(records[1].metrics[COST], value=amount),
    })
    report = evaluate_gate(documents, records, bundle)
    assert report["validation_errors"]
    assert_blocked(report)


def test_one_sided_records_retain_presence_only(documents, records):
    records[1] = replace(records[1], project_id="SYNTHETIC-LATER-ONLY")
    report = evaluate_gate(documents, records, empty_bundle())
    assert report["summary"]["earlier_only"] == report["summary"]["later_only"] == 1
    assert {row["presence"] for row in report["unmatched_records"]} == {"earlier_only", "later_only"}
    assert all(set(row) == {"project_id", "source_ref", "presence", "reason"}
               for row in report["unmatched_records"])
    assert_blocked(report)


def test_result_is_deterministic_under_record_order(documents, records):
    bundle = approval(records)
    first = evaluate_gate(documents, records, bundle)
    second = evaluate_gate(documents, list(reversed(records)), deepcopy(bundle))
    assert serialize_report(first) == serialize_report(second)


def test_all_public_views_use_gate_results(documents, records):
    report = evaluate_gate(documents, records, empty_bundle())
    view = select_view(report, section="approved_comparisons", project_id=records[0].project_id)
    assert view["approved_comparisons"] == []
    assert view["summary"]["held"] == 1
    assert select_view(report, section="held_pairs")["held_pairs"][0]["review_status"] == "held"
    with pytest.raises(ValueError, match="Unknown audit section"):
        select_view(report, section="ungated_changes")


def test_approval_does_not_leak_to_another_pair(documents, records):
    bundle = approval(records)
    additional = [replace(row, row_ordinal=2, project_id="SYNTHETIC-2") for row in records]
    report = evaluate_gate(documents, records + additional, bundle)
    assert report["summary"]["held"] == report["summary"]["approved"] == 1
    assert {row["project_id"] for row in report["approved_comparisons"]} == {"SYNTHETIC-1"}
    assert {row["project_id"] for row in report["held_pairs"]} == {"SYNTHETIC-2"}


def test_late_metric_error_cannot_leave_an_earlier_grant_visible(documents, records):
    bundle = approval(records)
    additional = [replace(row, row_ordinal=2, project_id="SYNTHETIC-2") for row in records]
    second = approval(additional)
    second["decisions"][0]["decision_id"] = "synthetic-second"
    for evidence in second["evidence"]:
        evidence["evidence_id"] = "second-" + evidence["evidence_id"]
    second["decisions"][0]["evidence_ids"] = [row["evidence_id"] for row in second["evidence"]]
    bundle["decisions"].extend(second["decisions"])
    bundle["evidence"].extend(second["evidence"])
    additional[1] = replace(additional[1], metrics={})
    report = evaluate_gate(documents, records + additional, bundle)
    assert any(error["code"] == "approval_metric_missing" for error in report["validation_errors"])
    assert report["summary"]["held"] == 2
    assert_blocked(report)


def test_budget_approval_cannot_authorize_estimated_cost(documents, records):
    report = evaluate_gate(documents, records, approval(records, metrics=(BUDGET,)))
    assert {row["metric"] for row in report["approved_comparisons"]} == {BUDGET}
    assert report["blocked_comparisons"][0]["metric"] == COST
