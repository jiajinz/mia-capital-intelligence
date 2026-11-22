"""HTML admission 2010 to 2017: structure, checks, holds and provenance. No network needed."""

import json
import re
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "traffic" / "traffic_monthly.html_2010_2017.v1.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HELD = {"2012-11", "2013-06", "2014-08", "2014-09"}


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_scope_is_82_months_with_both_measures_and_no_held_months():
    rows = load()["rows"]
    assert len(rows) == 164
    months = sorted({r["period"] for r in rows})
    assert len(months) == 82
    assert months[0] == "2010-01" and months[-1] == "2017-05"
    assert not (set(months) & HELD)
    assert "2010-07" not in months
    assert {r["measure"] for r in rows} == {"PASSENGERS", "TOTAL CARGO-TONS"}
    keys = [(r["period"], r["measure"]) for r in rows]
    assert len(keys) == len(set(keys))


def test_admission_record_is_owner_approved_and_timezone_aware():
    data = load()
    assert data["status"] == "admitted" and data["admitted_by"] == "owner"
    stamp = datetime.fromisoformat(data["admitted_at"].replace("Z", "+00:00"))
    assert stamp.tzinfo is not None


def test_passenger_rows_reconcile_printed_components():
    for r in load()["rows"]:
        if r["measure"] != "PASSENGERS":
            continue
        p = r["printed"]
        assert p["deplaned"] + p["enplaned"] == p["total"] == r["value"], r["period"]
        assert r["checks"]["passengers_dep_plus_enp_equals_total"] is True


def test_provenance_is_the_html_page_hash_and_official_url():
    for r in load()["rows"]:
        assert HEX64.match(r["source_html_sha256"]), r["period"]
        assert r["source_url"].startswith("https://www.miami-airport.com/monthly_traffic_")
        assert r["source_type"] == "html_monthly_page"
        assert r["table_block"] == "COMBINED TOTALS"


def test_held_months_are_recorded_not_admitted():
    assert set(load()["held_months"]) == HELD
