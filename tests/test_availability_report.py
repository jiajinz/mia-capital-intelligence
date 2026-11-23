"""Schedule accounting for the app-availability workflow, from synthetic run lists."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "availability_report.py"
SPEC = importlib.util.spec_from_file_location("availability_report_cli", SCRIPT)
assert SPEC and SPEC.loader
report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report)


def run(created: str, event: str = "schedule", conclusion: str = "success", status: str = "completed") -> dict:
    return {"createdAt": created, "event": event, "conclusion": conclusion, "status": status}


def complete_day() -> list[dict]:
    return [
        run("2026-11-18T00:19:04Z"),
        run("2026-11-18T06:17:30Z"),
        run("2026-11-18T12:21:10Z"),
        run("2026-11-18T18:16:02Z"),
    ]


def two_missed_slots() -> list[dict]:
    # 18 Nov: 06:17 and 12:17 are missing. 19 Nov is complete.
    return [
        run("2026-11-18T00:17:40Z"),
        run("2026-11-18T18:17:12Z"),
        run("2026-11-19T00:18:01Z"),
        run("2026-11-19T06:17:55Z"),
        run("2026-11-19T12:17:20Z"),
        run("2026-11-19T18:17:31Z"),
    ]


def write_json(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "runs.json"
    path.write_text(payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8")
    return path


def test_complete_day_has_no_missed_slots(tmp_path, capsys):
    path = write_json(tmp_path, complete_day())
    assert report.main([str(path)]) == 0
    out = capsys.readouterr().out
    assert "Scheduled runs: 4" in out
    assert "Expected six-hourly slots: 4" in out
    assert "Missed slots: 0" in out
    assert "Slots with two or more runs: 0" in out
    assert "Scheduled conclusions: success 4" in out
    assert "Manual runs (workflow_dispatch): 0" in out


def test_day_with_two_missed_slots_reports_both_gaps(tmp_path, capsys):
    path = write_json(tmp_path, two_missed_slots())
    assert report.main([str(path)]) == 0
    out = capsys.readouterr().out
    assert "Scheduled runs: 6" in out
    assert "Expected six-hourly slots: 8" in out
    assert "Missed slots: 2" in out
    assert "  17.99 h  2026-11-18 00:17 -> 2026-11-18 18:17" in out


def test_missed_slot_count_matches_the_grid_directly():
    runs = report.parse_runs(two_missed_slots())
    summary = report.summarize_schedule([r for r in runs if r.event == "schedule"])
    assert (summary.scheduled, summary.expected, summary.missed) == (6, 8, 2)
    assert summary.gaps[0][0] == pytest.approx(17.99, abs=0.01)


@pytest.mark.parametrize("payload", [
    "{not json",
    {"runs": []},
    ["not an object"],
    [{"createdAt": "2026-11-18T00:17:00Z", "event": "schedule", "conclusion": "success"}],
    [run("2026-11-18 00:17:00")],
    [run("2026-11-18T00:17:00")],
    [run("yesterday")],
    [{**run("2026-11-18T00:17:00Z"), "event": 7}],
])
def test_malformed_file_exits_two(tmp_path, capsys, payload):
    path = write_json(tmp_path, payload)
    assert report.main([str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error:")


def test_missing_file_exits_two(tmp_path, capsys):
    assert report.main([str(tmp_path / "absent.json")]) == 2
    assert "error:" in capsys.readouterr().err


def test_manual_runs_are_excluded_from_the_schedule_count(tmp_path, capsys):
    # The manual run at 06:20 sits inside the missed 06:17 slot but must not fill it.
    payload = two_missed_slots()[:2] + [
        run("2026-11-18T06:20:00Z", event="workflow_dispatch", conclusion="success"),
        run("2026-11-18T12:05:00Z", event="workflow_dispatch", conclusion="failure"),
    ]
    path = write_json(tmp_path, payload)
    assert report.main([str(path)]) == 0
    out = capsys.readouterr().out
    assert "Scheduled runs: 2" in out
    assert "Expected six-hourly slots: 4" in out
    assert "Missed slots: 2" in out
    assert "Manual runs (workflow_dispatch): 2" in out
    assert "Manual conclusions: failure 1, success 1" in out


def test_in_progress_run_is_labelled_by_status(tmp_path, capsys):
    payload = [run("2026-11-18T00:17:00Z", conclusion="", status="in_progress")]
    path = write_json(tmp_path, payload)
    assert report.main([str(path)]) == 0
    assert "Scheduled conclusions: in_progress 1" in capsys.readouterr().out


def test_empty_list_is_valid_and_has_no_slots(tmp_path, capsys):
    path = write_json(tmp_path, [])
    assert report.main([str(path)]) == 0
    assert "Scheduled runs: 0 (no slots to evaluate)" in capsys.readouterr().out
