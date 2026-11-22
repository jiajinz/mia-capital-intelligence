"""Failure modes of the offline monthly traffic candidate pipeline."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from mia_capital_intelligence import traffic_pilot as traffic

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "traffic_pilot.py"
SPEC = importlib.util.spec_from_file_location("traffic_pilot_cli", SCRIPT)
assert SPEC and SPEC.loader
cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cli)


def page_lines(extra_passenger=0, year_label=2024, trailing_cytd=True, month_end_day=31):
    lines = []

    def line(text, positions=None):
        words = text.split()
        xs = positions if positions else range(len(words))
        cells = [dict(text=w, x0=x, x1=x + 2, top=len(lines) * 10) for w, x in zip(words, xs, strict=True)]
        lines.append((text, cells))

    line("MIAMI INTERNATIONAL AIRPORT - TRAFFIC REPORT")
    line(f"MONTH ENDED: JANUARY {month_end_day}, 2025")
    for market in traffic.MARKETS:
        combined = market == "COMBINED TOTALS"
        line("% CHG OVR 2025 2024 % CHG OVR")
        suffix = " CYTD" if trailing_cytd else ""
        header = f"{market} DEPLANED ENPLANED TOTAL JAN 24 JAN 24 CYTD CYTD {year_label}{suffix}"
        positions = [10] * len(market.split()) + [100, 150, 200, 250, 260, 300, 310, 350, 400, 445, 450]
        line(header, positions if trailing_cytd else positions[:-1])
        for measure in traffic.MEASURES:
            amount = (2 if combined else 1) * (2 if measure == "TOTAL CARGO-TONS" else 1)
            extra = extra_passenger if measure == "PASSENGERS" and market != "DOMESTIC" else 0
            total = 2 * amount + extra
            values = f"{amount+extra} {amount} {total} 2 0 {total} 2 0"
            line(f"{measure} {values}", [10] * len(measure.split()) + list(range(100, 500, 50)))
    return lines


def test_january_cytd_at_wrong_position_even_when_values_equal():
    lines = page_lines()
    row = next(cells for text, cells in lines if text.startswith("PASSENGERS "))
    row[3], row[6] = row[6], row[3]
    with pytest.raises(ValueError, match="outside printed TOTAL"):
        traffic.extract_rows(lines, "2025-01")


def test_conflicting_trailing_year_holds_only_comparison_field():
    rows = traffic.extract_rows(page_lines(year_label=2023), "2025-01")
    assert len(rows) == 18
    assert all(row["held_fields"] == ["cytd_yoy_pct"] for row in rows)
    assert rows[0]["value"] == 2


def test_only_revised_month_reparsed_and_old_candidate_preserved(tmp_path, monkeypatch):
    periods = ["2025-01", "2025-02"]
    monkeypatch.setattr(cli, "PERIODS", periods)
    sources = {}
    calls = []

    def put(period, revision):
        body = f"{period}:{revision}".encode()
        digest = hashlib.sha256(body).hexdigest()
        sources[period] = dict(url="https://www.miami-airport.com/test.pdf", sha256=digest)
        cli.write_file(tmp_path / "pdfs" / (digest + ".pdf"), body)
        cli.write_json(tmp_path / "sources.json", sources)

    def decode(body, period):
        calls.append(period)
        lines = page_lines(extra_passenger=int(body[-1:]))
        return traffic.extract_rows(lines, "2025-01")

    monkeypatch.setattr(traffic, "read_page", decode)
    for period in periods:
        put(period, 0)
    assert cli.run_pilot(tmp_path)["cache_hits"] == 0
    before = (tmp_path / "candidate.json").read_bytes()
    assert cli.run_pilot(tmp_path)["cache_hits"] == 2
    assert (tmp_path / "candidate.json").read_bytes() == before
    put("2025-02", 1)
    report = cli.run_pilot(tmp_path)
    assert calls == [*periods, "2025-02"]
    assert list(report["revisions"]) == ["2025-02"]
    changed = report["revisions"]["2025-02"]
    assert "YoY 2026-02" in changed["monthly_outputs_to_recheck"]
    assert any(c["column"] == "month_total" and c["before"] == "4" and c["after"] == "5"
               for c in changed["changes"])
    assert any(json.loads(f.read_bytes()) == json.loads(before) for f in (tmp_path / "snapshots").glob("*.json"))


def test_header_without_trailing_cytd_is_accepted():
    rows = traffic.extract_rows(page_lines(trailing_cytd=False), "2025-01")
    assert len(rows) == 18
    assert all(row["held_fields"] == [] for row in rows)
    assert rows[0]["month_end_note"] is None


def test_printed_month_end_differing_from_calendar_is_kept_and_noted():
    rows = traffic.extract_rows(page_lines(month_end_day=30), "2025-01")
    assert rows[0]["period_evidence"] == "MONTH ENDED: JANUARY 30, 2025"
    assert rows[0]["month_end_note"] == "printed month-end 30 differs from calendar 31"


def test_wrong_printed_month_still_rejected():
    lines = page_lines()
    lines[1] = ("MONTH ENDED: FEBRUARY 28, 2025", lines[1][1])
    with pytest.raises(ValueError, match="printed month-end"):
        traffic.extract_rows(lines, "2025-01")
