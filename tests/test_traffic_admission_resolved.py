"""Resolved admission 2012-11, 2014-08, 2014-09: structure, corroboration and notes. No network needed."""

import json
import re
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "traffic" / "traffic_monthly.resolved_2012_2014.v1.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_scope_is_three_months_with_both_measures_and_2013_06_stays_out():
    rows = load()["rows"]
    assert len(rows) == 6
    assert sorted({r["period"] for r in rows}) == ["2012-11", "2014-08", "2014-09"]
    assert "2013-06" not in {r["period"] for r in rows}
    assert {r["measure"] for r in rows} == {"PASSENGERS", "TOTAL CARGO-TONS"}


def test_admission_record_is_owner_approved_and_timezone_aware():
    data = load()
    assert data["status"] == "admitted" and data["admitted_by"] == "owner"
    assert datetime.fromisoformat(data["admitted_at"].replace("Z", "+00:00")).tzinfo is not None


def test_each_row_has_html_provenance_and_corroboration():
    for r in load()["rows"]:
        assert HEX64.match(r["source_html_sha256"]), r["period"]
        assert r["source_url"].startswith("https://www.miami-airport.com/monthly_traffic_")
        assert r["corroboration"] == "annual COMBINED total (yearly traffic page)"
        assert r["held_fields"] == []


def test_unreliable_cells_are_described_and_not_stored():
    rows = load()["rows"]
    for r in rows:
        assert "deplaned" not in r and "enplaned" not in r and "cytd" not in r
    notes = {r["period"]: r["notes"] for r in rows}
    assert "do not reconcile" in notes["2012-11"] and "not stored" in notes["2012-11"]
    assert "CYTD cell is not stored" in notes["2014-08"]
    assert "rounding" in notes["2014-09"]
