"""Seats and aircraft movements admitted with the traffic series. Structure and provenance only."""

import json
import re
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "traffic" / "traffic_capacity.v1.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_scope_matches_the_199_admitted_months():
    rows = load()["rows"]
    months = sorted({r["period"] for r in rows})
    assert len(months) == 199
    assert "2013-06" not in months and "2010-07" not in months
    assert len(rows) == 2 * len(months)
    assert {r["measure"] for r in rows} == {"SEATS", "COMMERCIAL AIRCRAFT MVMT"}


def test_admission_record_is_owner_approved_and_timezone_aware():
    data = load()
    assert data["status"] == "admitted" and data["admitted_by"] == "owner"
    assert datetime.fromisoformat(data["admitted_at"].replace("Z", "+00:00")).tzinfo is not None


def test_every_row_has_a_source_hash_and_url_and_positive_value():
    for r in load()["rows"]:
        assert HEX64.match(r["source_sha256"]), r["period"]
        assert r["source_url"].startswith("https://www.miami-airport.com/"), r["period"]
        assert isinstance(r["value"], int) and r["value"] > 0


def test_later_report_months_are_identified_as_such():
    later = [r for r in load()["rows"] if r["value_column"] == "same_month_prior_year"]
    assert {r["period"] for r in later} == {"2017-12", "2018-10", "2022-06"}
    assert len(later) == 6
