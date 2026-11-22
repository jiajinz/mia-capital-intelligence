"""Gap admission 2015-10, 2016-02 and 2017-06 to 2017-12: structure and provenance. No PDFs needed."""

import json
import re
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "traffic" / "traffic_monthly.gap_2015_2017.v1.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MONTHS = {"2015-10", "2016-02", "2017-06", "2017-07", "2017-08", "2017-09", "2017-10", "2017-11", "2017-12"}


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_scope_is_nine_months_with_both_measures():
    rows = load()["rows"]
    assert len(rows) == 18
    assert {r["period"] for r in rows} == MONTHS
    assert {r["measure"] for r in rows} == {"PASSENGERS", "TOTAL CARGO-TONS"}
    keys = [(r["period"], r["measure"]) for r in rows]
    assert len(keys) == len(set(keys))


def test_admission_record_is_owner_approved_and_timezone_aware():
    data = load()
    assert data["status"] == "admitted" and data["admitted_by"] == "owner"
    assert datetime.fromisoformat(data["admitted_at"].replace("Z", "+00:00")).tzinfo is not None


def test_each_row_has_pdf_provenance_and_two_printed_header_lines():
    for r in load()["rows"]:
        assert HEX64.match(r["source_sha256"]), r["period"]
        assert r["source_url"].startswith("https://www.miami-airport.com/")
        assert r["pdf_page_index"] == 0
        assert len(r["table_header_lines"]) == 2 and r["table_header_lines"][0].startswith("% CHG OVR")
        assert r["period_evidence"].startswith("MONTH ENDED:")


def test_2017_12_is_taken_from_the_following_report_prior_year_column():
    rows = [r for r in load()["rows"] if r["period"] == "2017-12"]
    assert len(rows) == 2
    for r in rows:
        assert r["value_column"] == "same_month_prior_year"
        assert r["later_report_period"] == "2018-12"
        assert r["vintage"]["first_published"]["status"] == "not_obtained"
    assert {r["measure"]: r["value"] for r in rows} == {"PASSENGERS": 3997071, "TOTAL CARGO-TONS": 218248}


def test_no_revision_stamp_and_only_the_2017_08_cytd_hold():
    rows = load()["rows"]
    assert all(r["vintage"]["revision_stamp_printed"] is False for r in rows)
    held = [r for r in rows if r["held_fields"]]
    assert {r["period"] for r in held} == {"2017-08"}
    assert all(r["held_fields"] == ["cytd_yoy_pct"] for r in held)
    assert len(held) == 2  # monthly values stay admitted
