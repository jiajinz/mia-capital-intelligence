"""Fail-closed, metric-specific review validation and DuckDB query boundary."""

import json
import re
from collections import Counter
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import duckdb
from jsonschema import Draft202012Validator, FormatChecker

from mia_capital_intelligence.comparability_model import (
    CONTRACT_VERSION,
    EVIDENCE_CATEGORIES,
    SUPPORTED_METRICS,
    SourceDocument,
    SourceRecord,
    candidate_id,
)

ROOT = Path(__file__).resolve().parents[2]
SQL = Path(__file__).with_name("sql")


def _error(code: str, location: str, message: str) -> dict[str, str]:
    return {"code": code, "location": location, "message": message}


def _source_errors(
    documents: tuple[SourceDocument, SourceDocument], records: list[SourceRecord]
) -> list[dict[str, str]]:
    errors = []
    earlier, later = documents
    if earlier.matter_id == later.matter_id or earlier.period_end >= later.period_start:
        errors.append(_error("period_order", "documents", "Expected distinct ordered, nonoverlapping reports"))
    documents_by_id = {doc.matter_id: doc for doc in documents}
    for doc in documents:
        if doc.period_start > doc.period_end or not re.fullmatch(r"[0-9a-f]{64}", doc.sha256):
            errors.append(_error("source_document", doc.matter_id, "Invalid period or checksum"))
    refs = Counter(record.source_ref for record in records)
    keys = Counter((record.matter_id, record.exhibit, record.project_id) for record in records)
    for record in records:
        location = record.source_ref
        doc = documents_by_id.get(record.matter_id)
        if (
            doc is None or record.document_sha256 != doc.sha256 or record.exhibit != "B"
            or record.pdf_page not in doc.exhibit_pages or record.row_ordinal < 1
            or not record.project_id.strip() or not record.description_raw.strip()
        ):
            errors.append(_error("source_reference", location, "Source version, row, exhibit or identity is invalid"))
        if refs[location] != 1 or keys[(record.matter_id, record.exhibit, record.project_id)] != 1:
            errors.append(_error("source_duplicate", location, "Duplicate source row or candidate key"))
        for metric, observation in record.metrics.items():
            amount = observation.value
            valid_amount = amount is None or (
                isinstance(amount, Decimal) and amount.is_finite()
                and abs(amount) < Decimal("10000000000000000")
                and amount == amount.quantize(Decimal("0.01"))
            )
            if (
                metric not in SUPPORTED_METRICS or not valid_amount or observation.unit != "USD"
                or observation.verification_status not in {"machine_cross_checked", "visually_verified"}
                or not observation.original_header.strip()
            ):
                errors.append(_error("source_metric", location, f"Invalid metric observation: {metric}"))
    return errors


def _is_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})", value
    ):
        return False
    return datetime.fromisoformat(value.upper().replace("Z", "+00:00")).utcoffset() is not None


def _schema_errors(bundle: Any, schema_path: Path) -> list[dict[str, str]]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    checker = FormatChecker()
    checker.checks("date-time", raises=(ValueError, TypeError))(_is_timestamp)
    validator = Draft202012Validator(schema, format_checker=checker)
    return [
        _error("review_schema", "/" + "/".join(map(str, error.absolute_path)), error.message)
        for error in sorted(validator.iter_errors(bundle), key=lambda item: str(list(item.absolute_path)))
    ]


def _review_errors(bundle: dict[str, Any], pairs: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    errors = []
    for collection, field in (("decisions", "decision_id"), ("decisions", "candidate_id"),
                              ("evidence", "evidence_id")):
        for identifier, count in sorted(Counter(row[field] for row in bundle[collection]).items()):
            if count > 1:
                errors.append(_error("review_duplicate", identifier, f"Repeated {collection}.{field}"))
    evidence_by_id = {row["evidence_id"]: row for row in bundle["evidence"]}
    for evidence in bundle["evidence"]:
        pair = pairs.get(evidence["candidate_id"])
        if pair is None or set(evidence["source_refs"]) != {pair["earlier_ref"], pair["later_ref"]}:
            errors.append(_error("evidence_reference", evidence["evidence_id"], "Evidence must bind both current source rows"))
    for decision in bundle["decisions"]:
        pair = pairs.get(decision["candidate_id"])
        if pair is None or (
            decision["earlier_source_ref"], decision["later_source_ref"]
        ) != (pair["earlier_ref"], pair["later_ref"]):
            errors.append(_error("decision_reference", decision["decision_id"], "Decision references a different source pair"))
        for evidence_id in decision["evidence_ids"]:
            evidence = evidence_by_id.get(evidence_id)
            if evidence is None or evidence["candidate_id"] != decision["candidate_id"]:
                errors.append(_error("decision_evidence", decision["decision_id"], f"Invalid evidence link: {evidence_id}"))
        if decision["outcome"] == "comparable":
            linked = [evidence_by_id[eid] for eid in decision["evidence_ids"] if eid in evidence_by_id]
            decision_time = datetime.fromisoformat(decision["decided_at"].upper().replace("Z", "+00:00"))
            for metric in decision["approved_metrics"]:
                confirmed = {
                    evidence["category"] for evidence in linked
                    if evidence["verification_status"] == "verified"
                    and evidence["metric"] in {None, metric}
                    and (evidence["category"] not in {"financial_metric", "estimate_basis"}
                         or evidence["metric"] == metric)
                    and datetime.fromisoformat(evidence["verified_at"].upper().replace("Z", "+00:00")) <= decision_time
                }
                missing = sorted(set(EVIDENCE_CATEGORIES) - confirmed)
                if missing:
                    errors.append(_error(
                        "approval_incomplete", decision["decision_id"],
                        f"{metric}: missing verified evidence for {', '.join(missing)}",
                    ))
    return errors


def _insert_sources(connection: duckdb.DuckDBPyConnection, records: list[SourceRecord]) -> None:
    connection.execute("""
        CREATE TABLE source_rows (
            source_ref VARCHAR PRIMARY KEY, matter_id VARCHAR, exhibit VARCHAR, project_id VARCHAR
        );
        CREATE TABLE source_amounts (
            source_ref VARCHAR, metric VARCHAR, amount DECIMAL(18,2), unit VARCHAR,
            PRIMARY KEY (source_ref, metric)
        );
        CREATE TABLE eligible_metrics (
            candidate_id VARCHAR, project_id VARCHAR, metric VARCHAR, decision_id VARCHAR,
            reviewer VARCHAR, earlier_ref VARCHAR, later_ref VARCHAR, outcome VARCHAR,
            PRIMARY KEY (candidate_id, metric)
        );
    """)
    if records:
        connection.executemany(
            "INSERT INTO source_rows VALUES (?, ?, ?, ?)",
            [(row.source_ref, row.matter_id, row.exhibit, row.project_id) for row in records],
        )
    amounts = [(row.source_ref, name, value.value, value.unit)
               for row in records for name, value in sorted(row.metrics.items())]
    if amounts:
        connection.executemany("INSERT INTO source_amounts VALUES (?, ?, ?, ?)", amounts)


def _page_controls(records: list[SourceRecord]) -> list[dict[str, Any]]:
    controls = []
    pages = sorted({(row.matter_id, row.exhibit, row.pdf_page) for row in records})
    for matter, exhibit, page in pages:
        rows = [row for row in records if (row.matter_id, row.exhibit, row.pdf_page) == (matter, exhibit, page)]
        amounts = [row.metrics.get("total_estimated_cost_usd") for row in rows]
        controls.append({
            "matter_id": matter, "exhibit": exhibit, "pdf_page": page,
            "row_count": len(rows),
            "numeric_estimate_sum_usd": sum(
                (amount.value for amount in amounts if amount is not None and amount.value is not None),
                Decimal(0),
            ),
            "missing_estimates": sum(amount is None or amount.value is None for amount in amounts),
        })
    return controls


def evaluate_gate(
    documents: tuple[SourceDocument, SourceDocument],
    records: list[SourceRecord],
    review_bundle: dict[str, Any],
    *,
    schema_path: Path = ROOT / "schemas/review_dispositions.schema.json",
) -> dict[str, Any]:
    """Return audited views. Any technical error empties the eligibility relation."""
    report: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "independence_disclosure": "Independent portfolio project with no affiliation with MDAD or HNTB",
        "review_schema_sha256": sha256(schema_path.read_bytes()).hexdigest(),
        "review_bundle_sha256": sha256(json.dumps(review_bundle, sort_keys=True).encode()).hexdigest(),
        "documents": [asdict(doc) for doc in documents],
        "source_observations": [
            {"source_ref": row.source_ref, **asdict(row), "printed_page": f"MDC{row.pdf_page:03}",
             "pdf_page_index": row.pdf_page - 1, "freeze_date": None,
             "transformation": "Preserve source text; parse reported USD exactly as Decimal"}
            for row in sorted(records, key=lambda value: value.source_ref)
        ],
        "candidates": [], "held_pairs": [], "approved_comparisons": [],
        "excluded_pairs": [], "unmatched_records": [], "blocked_comparisons": [],
        "validation_errors": _source_errors(documents, records),
    }
    if report["validation_errors"]:
        report["summary"] = {"source_rows": len(records), "candidate_pairs": 0,
                             "held": 0, "approved": 0, "excluded": 0,
                             "approved_metrics": 0, "input_valid": False}
        return report

    report["page_controls"] = _page_controls(records)

    schema_errors = _schema_errors(review_bundle, schema_path)
    report["validation_errors"].extend(schema_errors)
    report["submitted_review_bundle"] = review_bundle
    # Invalid review shapes remain in the audit, but supply zero eligible decisions.
    validated_bundle = review_bundle if not schema_errors else {"evidence": [], "decisions": []}

    by_ref = {row.source_ref: row for row in records}
    with duckdb.connect(":memory:") as connection:
        _insert_sources(connection, records)
        matched = connection.execute(
            (SQL / "candidates.sql").read_text(), [doc.matter_id for doc in documents]
        ).fetchall()
        for project_id, earlier_ref, later_ref in matched:
            if earlier_ref is None or later_ref is None:
                report["unmatched_records"].append({
                    "project_id": project_id, "source_ref": earlier_ref or later_ref,
                    "presence": "later_only" if earlier_ref is None else "earlier_only",
                    "reason": "Listed in only one selected Exhibit B report",
                })
            else:
                report["candidates"].append({
                    "candidate_id": candidate_id(earlier_ref, later_ref), "project_id": project_id,
                    "earlier_ref": earlier_ref, "later_ref": later_ref,
                    "matching_method": "same_exhibit_exact_project_id",
                    "default_review_status": "held",
                    "earlier_period": {
                        "start": documents[0].period_start, "end": documents[0].period_end,
                    },
                    "later_period": {
                        "start": documents[1].period_start, "end": documents[1].period_end,
                    },
                })
        pairs = {row["candidate_id"]: row for row in report["candidates"]}
        report["validation_errors"].extend(_review_errors(validated_bundle, pairs))
        decisions = {row["candidate_id"]: row for row in validated_bundle["decisions"]}
        eligible = []
        for pair in report["candidates"]:
            decision = decisions.get(pair["candidate_id"])
            outcome = decision["outcome"] if decision else "held"
            reason = decision["rationale"] if decision else "No explicit identity, scope, metric, basis and period approval"
            if report["validation_errors"]:
                outcome, reason = "held", "Technical validation failed; all approvals in this bundle are blocked"
            pair["review_status"] = outcome
            pair["reason"] = reason
            pair["decision_id"] = decision["decision_id"] if decision else None
            pair["reviewer"] = decision["reviewer"] if decision else None
            pair["decided_at"] = decision["decided_at"] if decision else None
            approved_metrics = decision["approved_metrics"] if outcome == "comparable" else []
            pair["approved_metrics"] = list(approved_metrics)
            observed_metrics = set(by_ref[pair["earlier_ref"]].metrics) | set(by_ref[pair["later_ref"]].metrics)
            pair["comparability_checks"] = {
                metric: {
                    category: "confirmed_by_explicit_review" if metric in approved_metrics else "unconfirmed"
                    for category in EVIDENCE_CATEGORIES
                }
                for metric in sorted(observed_metrics)
            }
            for metric in sorted(approved_metrics):
                earlier = by_ref[pair["earlier_ref"]].metrics.get(metric)
                later = by_ref[pair["later_ref"]].metrics.get(metric)
                if earlier is None or later is None or earlier.value is None or later.value is None:
                    report["validation_errors"].append(_error(
                        "approval_metric_missing", pair["candidate_id"], f"Two usable observations required for {metric}"
                    ))
                else:
                    eligible.append((
                        pair["candidate_id"], pair["project_id"], metric, decision["decision_id"],
                        decision["reviewer"], pair["earlier_ref"], pair["later_ref"], outcome,
                    ))
            for metric in sorted(observed_metrics - set(approved_metrics)):
                report["blocked_comparisons"].append({
                    "candidate_id": pair["candidate_id"], "project_id": pair["project_id"],
                    "metric": metric, "reason": reason if outcome != "comparable" else "Metric has no explicit approval",
                })
        # Grants are inserted only after ALL review/source/metric validation has succeeded.
        if not report["validation_errors"] and eligible:
            connection.executemany("INSERT INTO eligible_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?)", eligible)
        result = connection.execute((SQL / "approved_metrics.sql").read_text())
        columns = [column[0] for column in result.description]
        report["approved_comparisons"] = [dict(zip(columns, row, strict=True)) for row in result.fetchall()]

    # A late technical failure also invalidates the disposition presentation.
    if report["validation_errors"]:
        for pair in report["candidates"]:
            pair.update(review_status="held", approved_metrics=[],
                        comparability_checks={
                            metric: {category: "unconfirmed" for category in EVIDENCE_CATEGORIES}
                            for metric in pair["comparability_checks"]
                        }, decision_id=None, reviewer=None, decided_at=None,
                        reason="Technical validation failed; all approvals in this bundle are blocked")
        report["blocked_comparisons"] = [
            {"candidate_id": pair["candidate_id"], "project_id": pair["project_id"],
             "metric": metric, "reason": pair["reason"]}
            for pair in report["candidates"]
            for metric in sorted(set(by_ref[pair["earlier_ref"]].metrics) | set(by_ref[pair["later_ref"]].metrics))
        ]
    report["held_pairs"] = [pair for pair in report["candidates"] if pair["review_status"] == "held"]
    report["excluded_pairs"] = [pair for pair in report["candidates"] if pair["review_status"] == "excluded"]
    report["summary"] = {
        "source_rows": len(records), "candidate_pairs": len(report["candidates"]),
        "held": len(report["held_pairs"]),
        "approved": sum(pair["review_status"] == "comparable" for pair in report["candidates"]),
        "excluded": len(report["excluded_pairs"]),
        "approved_metrics": len(report["approved_comparisons"]),
        "earlier_only": sum(row["presence"] == "earlier_only" for row in report["unmatched_records"]),
        "later_only": sum(row["presence"] == "later_only" for row in report["unmatched_records"]),
        "input_valid": not report["validation_errors"],
    }
    return report
