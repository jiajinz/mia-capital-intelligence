"""Admitted traffic values: structure, scope, hold, vintage and provenance. No PDFs are needed."""

import json
import re
from datetime import datetime
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "data" / "traffic" / "traffic_monthly.plan_a.v1.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


@pytest.fixture(scope="module")
def dataset():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_scope_is_the_66_verified_combined_values(dataset):
    rows = dataset["rows"]
    assert len(rows) == 66
    assert {r["market"] for r in rows} == {"COMBINED TOTALS"}
    assert {r["measure"] for r in rows} == {"PASSENGERS", "TOTAL CARGO-TONS"}
    periods = sorted({r["period"] for r in rows})
    assert len(periods) == 33 and periods[0] == "2024-01" and periods[-1] == "2026-09"


def test_each_period_and_measure_appears_once(dataset):
    keys = [(r["period"], r["measure"]) for r in dataset["rows"]]
    assert len(keys) == len(set(keys))


def test_every_row_is_admitted_with_integer_values(dataset):
    assert all(r["status"] == "admitted" for r in dataset["rows"])
    assert all(isinstance(r["value"], int) and r["value"] >= 0 for r in dataset["rows"])


def test_hold_is_limited_to_the_two_cytd_months(dataset):
    held_rows = [r for r in dataset["rows"] if r["held_fields"]]
    assert {r["period"] for r in held_rows} == {"2024-12", "2025-06"}
    assert all(r["held_fields"] == ["cytd_yoy_pct"] for r in held_rows)
    assert len(held_rows) == 4  # two measures in each of the two held months
    assert all(r["held_fields"] == [] for r in dataset["rows"] if r["period"] not in {"2024-12", "2025-06"})


def test_provenance_is_complete_and_hashed(dataset):
    for r in dataset["rows"]:
        assert HEX64.match(r["source_sha256"]), r["period"]
        assert r["source_url"].startswith("https://www.miami-airport.com/")
        assert r["pdf_page_index"] == 0
        assert r["period_evidence"].startswith("MONTH ENDED:")
        assert len(r["table_header_lines"]) == 2 and r["table_header_lines"][0].startswith("% CHG OVR")


def test_vintage_rules_match_the_owner_decisions(dataset):
    march = [r for r in dataset["rows"] if r["period"] == "2025-03"]
    assert len(march) == 2
    for r in march:
        assert r["vintage"]["first_published"]["status"] == "not_obtained"
        assert r["vintage"]["revision_stamp_printed"] is True
    others = [r for r in dataset["rows"] if r["period"] != "2025-03"]
    assert all(r["vintage"]["first_published"]["status"] == "single_version_observed" for r in others)
    assert all(r["vintage"]["revision_stamp_printed"] is False for r in others)
    assert dataset["revision_rule"] == "two_vintages"


def test_admission_record_is_timezone_aware_and_owner_approved(dataset):
    assert dataset["admitted_by"] == "owner"
    stamp = datetime.fromisoformat(dataset["admitted_at"].replace("Z", "+00:00"))
    assert stamp.tzinfo is not None
    assert dataset["status"] == "admitted"


def test_footnote_is_recorded_as_unconfirmed_not_applied(dataset):
    flagged = [r for r in dataset["rows"] if r["footnotes"]]
    assert {r["period"] for r in flagged} == {"2024-05", "2024-06", "2024-07"}
    assert all("not confirmed" in r["footnotes"][0] for r in flagged)
