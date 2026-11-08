"""End-to-end gate verification over the pinned Exhibit B originals."""

import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from mia_capital_intelligence.comparability import evaluate_gate
from mia_capital_intelligence.review_gate import load_review_bundle, serialize_report
from mia_capital_intelligence.source_records import load_exhibit_b

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def real_audit():
    if any(not (ROOT / f"data/raw/{matter}.pdf").is_file() for matter in ("260526", "261402")):
        pytest.skip("Pinned local PDFs required for Stage 1A integration")
    documents, records = load_exhibit_b(ROOT)
    return evaluate_gate(documents, records, load_review_bundle(ROOT / "data/review_dispositions.json"))


@pytest.mark.integration
def test_real_counts_controls_and_no_approval_leakage(real_audit):
    assert real_audit["summary"] == {
        "source_rows": 222, "candidate_pairs": 107, "held": 107, "approved": 0,
        "excluded": 0, "approved_metrics": 0, "earlier_only": 3, "later_only": 5,
        "input_valid": True,
    }
    assert [(row["row_count"], row["numeric_estimate_sum_usd"], row["missing_estimates"])
            for row in real_audit["page_controls"]] == [
        (66, Decimal("2955660025"), 0), (44, Decimal("3446491140"), 0),
        (68, Decimal("3356850420"), 0), (44, Decimal("3406481145"), 0),
    ]
    assert real_audit["approved_comparisons"] == []
    assert len(real_audit["blocked_comparisons"]) == 107
    assert real_audit["submitted_review_bundle"]["decisions"] == []
    assert all(pair["review_status"] == "held" and not pair["approved_metrics"]
               and pair["reviewer"] is None and pair["decided_at"] is None
               for pair in real_audit["candidates"])
    payload = json.loads(serialize_report(real_audit))
    assert all(not any("delta" in key or "change_amount" in key for key in pair)
               for pair in payload["candidates"])


@pytest.mark.integration
def test_real_phase_and_d60_examples_are_held(real_audit):
    pairs = {row["project_id"]: row for row in real_audit["candidates"]}
    assert pairs["CA176A"]["review_status"] == pairs["T180B"]["review_status"] == "held"
    observations = {row["source_ref"]: row for row in real_audit["source_observations"]}
    seating = pairs["CA176A"]
    assert observations[seating["earlier_ref"]]["metrics"]["total_estimated_cost_usd"]["value"] == Decimal("3191832")
    assert observations[seating["later_ref"]]["metrics"]["total_estimated_cost_usd"]["value"] == Decimal("3191832")
    assert "Ph2" in observations[seating["later_ref"]]["description_raw"]
    one_sided = {row["project_id"]: row["presence"] for row in real_audit["unmatched_records"]}
    assert one_sided["CA176B"] == "later_only"
    assert one_sided["T180D"] == "earlier_only"


@pytest.mark.integration
def test_real_cli_invalid_status_returns_nonzero_and_no_approvals(tmp_path):
    if not (ROOT / "data/raw/261402.pdf").is_file():
        pytest.skip("Pinned local PDFs required")
    review_path = tmp_path / "bad_review.json"
    review_path.write_text('{"schema_version":"1.0","evidence":[],"decisions":[{"outcome":"approved"}]}')
    process = subprocess.run(
        [sys.executable, "-m", "mia_capital_intelligence.review_gate",
         "--reviews", str(review_path), "--section", "approved_comparisons"],
        cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        text=True, capture_output=True,
    )
    assert process.returncode == 1, process.stderr
    result = json.loads(process.stdout)
    assert result["approved_comparisons"] == []
    assert result["summary"]["held"] == 107
    assert result["validation_errors"]


def test_duplicate_json_fields_are_rejected(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema_version":"1.0","decisions":[],"decisions":[]}')
    with pytest.raises(ValueError, match="Duplicate JSON field: decisions"):
        load_review_bundle(path)
