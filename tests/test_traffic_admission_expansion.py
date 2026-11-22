"""Expansion admission 2018-01 to 2023-12: structure, provenance, holds and notes. No PDFs needed."""

import json
import re
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "traffic" / "traffic_monthly.expansion_2018_2023.v1.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SCANNED = {"2018-10", "2022-06"}
HELD = {"2018-04", "2019-08", "2019-12", "2021-11", "2022-09"}
CREW = {"2018-06", "2019-05", "2019-06", "2019-07", "2020-05", "2020-06", "2020-07", "2021-05", "2021-06",
        "2021-07", "2022-05", "2022-07", "2023-05", "2023-06", "2023-07"}


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_scope_is_72_months_with_both_measures():
    rows = load()["rows"]
    assert len(rows) == 144
    months = sorted({r["period"] for r in rows})
    assert len(months) == 72 and months[0] == "2018-01" and months[-1] == "2023-12"
    assert {r["market"] for r in rows} == {"COMBINED TOTALS"}
    assert {r["measure"] for r in rows} == {"PASSENGERS", "TOTAL CARGO-TONS"}
    keys = [(r["period"], r["measure"]) for r in rows]
    assert len(keys) == len(set(keys))


def test_admission_record_is_owner_approved_and_timezone_aware():
    data = load()
    assert data["status"] == "admitted" and data["admitted_by"] == "owner"
    stamp = datetime.fromisoformat(data["admitted_at"].replace("Z", "+00:00"))
    assert stamp.tzinfo is not None
    assert all(r["status"] == "admitted" for r in data["rows"])


def test_printed_rows_have_full_provenance():
    for r in load()["rows"]:
        if r["period"] in SCANNED:
            continue
        assert HEX64.match(r["source_sha256"]), r["period"]
        assert r["source_url"].startswith("https://www.miami-airport.com/")
        assert r["period_evidence"].startswith("MONTH ENDED:")
        assert len(r["table_header_lines"]) == 2 and r["table_header_lines"][0].startswith("% CHG OVR")
        assert isinstance(r["value"], int) and r["value"] > 0


def test_scanned_months_take_printed_values_from_the_following_report():
    rows = [r for r in load()["rows"] if r["period"] in SCANNED]
    assert len(rows) == 4
    expected = {("2018-10", "PASSENGERS"): 3327775, ("2018-10", "TOTAL CARGO-TONS"): 197515,
                ("2022-06", "PASSENGERS"): 4166556, ("2022-06", "TOTAL CARGO-TONS"): 209244}
    for r in rows:
        assert r["value"] == expected[(r["period"], r["measure"])]
        assert r["value_column"] == "same_month_prior_year"
        assert r["later_report_period"] == {"2018-10": "2019-10", "2022-06": "2023-06"}[r["period"]]
        assert HEX64.match(r["later_report_sha256"]) and HEX64.match(r["scanned_file_sha256"])
        assert r["vintage"]["first_published"]["status"] == "not_obtained"


def test_holds_match_the_reviewed_header_years():
    held = {r["period"] for r in load()["rows"] if r["held_fields"]}
    assert held == HELD
    assert all(r["held_fields"] == ["cytd_yoy_pct"] for r in load()["rows"] if r["period"] in HELD)


def test_notes_are_recorded_and_not_applied_to_values():
    rows = load()["rows"]
    crew = {r["period"] for r in rows if any("crew-totals footnote" in n for n in r["page_notes"])}
    assert crew == CREW
    assert {r["period"] for r in rows if any("market-definition footnote" in n for n in r["page_notes"])} == {
        "2018-05", "2018-06", "2018-07"}
    month_end = [r for r in rows if r.get("month_end_note")]
    assert {r["period"] for r in month_end} == {"2020-02"}
