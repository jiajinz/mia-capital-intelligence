"""Keep independent line and branch statistics distinct in coverage summaries."""

import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
report_summary = runpy.run_path(str(ROOT / "scripts/report_test_coverage.py"))["summary"]


def test_line_and_branch_rates_are_separate_from_combined_coverage():
    report = {"meta": {"branch_coverage": True}, "totals": {
        "covered_lines": 3, "num_statements": 4,
        "covered_branches": 1, "num_branches": 2, "percent_covered": 66.67,
    }, "files": {"sample.py": {}}}
    text = report_summary(report, "Synthetic coverage fixture")
    assert "75.00% (3/4 executable lines)" in text
    assert "50.00% (1/2 branch destinations)" in text
    assert "66.67%" not in text


def test_report_without_branch_measurement_is_rejected():
    with pytest.raises(ValueError, match="branch measurement"):
        report_summary({"meta": {"branch_coverage": False}}, "Fixture")


def test_zero_denominators_do_not_claim_full_coverage():
    report = {"meta": {"branch_coverage": True}, "totals": {
        "covered_lines": 0, "num_statements": 0, "covered_branches": 0, "num_branches": 0,
    }, "files": {}}
    assert "N/A (no branch destinations)" in report_summary(report, "Fixture")
