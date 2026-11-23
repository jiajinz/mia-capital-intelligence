"""Read-only report of scheduled app-availability runs against six-hourly slots.

Input is the JSON printed by:
  gh run list --workflow app-availability.yml --limit N --json createdAt,event,conclusion,status

This script never calls GitHub. Each scheduled run is matched to the nearest
slot (minute 17 at 00, 06, 12 and 18 UTC). Slots with no matched run are missed.
"""

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

SLOT_MINUTE = 17
SLOT_HOURS = (0, 6, 12, 18)
SLOT_SPACING = timedelta(hours=6)
SCHEDULE_EVENT = "schedule"
MANUAL_EVENT = "workflow_dispatch"
REQUIRED_KEYS = ("createdAt", "event", "conclusion", "status")
TOP_GAPS = 3
EXIT_OK = 0
EXIT_MALFORMED = 2


class MalformedInput(ValueError):
    """The run list does not have the shape that gh run list prints."""


@dataclass(frozen=True)
class Run:
    created: datetime
    event: str
    outcome: str


@dataclass(frozen=True)
class ScheduleSummary:
    scheduled: int
    expected: int
    missed: int
    duplicated: int
    first: datetime | None
    last: datetime | None
    gaps: tuple[tuple[float, datetime, datetime], ...]


def parse_created(value: object, index: int) -> datetime:
    if not isinstance(value, str):
        raise MalformedInput(f"run {index}: createdAt must be a string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise MalformedInput(f"run {index}: createdAt is not ISO 8601: {value!r}") from error
    if parsed.tzinfo is None:
        raise MalformedInput(f"run {index}: createdAt has no timezone: {value!r}")
    return parsed.astimezone(timezone.utc)


def parse_runs(data: object) -> list[Run]:
    if not isinstance(data, list):
        raise MalformedInput("top-level JSON value must be a list of runs")
    runs = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise MalformedInput(f"run {index}: must be an object")
        missing = [key for key in REQUIRED_KEYS if key not in item]
        if missing:
            raise MalformedInput(f"run {index}: missing keys {', '.join(missing)}")
        event, conclusion, status = item["event"], item["conclusion"], item["status"]
        if not isinstance(event, str) or not isinstance(status, str):
            raise MalformedInput(f"run {index}: event and status must be strings")
        if conclusion is not None and not isinstance(conclusion, str):
            raise MalformedInput(f"run {index}: conclusion must be a string or null")
        # gh prints an empty conclusion while a run is still in progress.
        outcome = conclusion or status
        runs.append(Run(parse_created(item["createdAt"], index), event, outcome))
    return runs


def nearest_slot(moment: datetime) -> datetime:
    day = moment.replace(hour=0, minute=0, second=0, microsecond=0)
    candidates = [day + timedelta(days=offset, hours=hour, minutes=SLOT_MINUTE)
                  for offset in (-1, 0, 1) for hour in SLOT_HOURS]
    return min(candidates, key=lambda slot: abs(slot - moment))


def summarize_schedule(scheduled: list[Run], top_gaps: int = TOP_GAPS) -> ScheduleSummary:
    if not scheduled:
        return ScheduleSummary(0, 0, 0, 0, None, None, ())
    times = sorted(run.created for run in scheduled)
    first_slot, last_slot = nearest_slot(times[0]), nearest_slot(times[-1])
    expected = int((last_slot - first_slot) / SLOT_SPACING) + 1
    hits = Counter(nearest_slot(moment) for moment in times)
    gaps = sorted(((b - a) / timedelta(hours=1), a, b) for a, b in zip(times, times[1:]))
    largest = tuple(sorted(gaps, key=lambda gap: gap[0], reverse=True)[:top_gaps])
    return ScheduleSummary(
        scheduled=len(times),
        expected=expected,
        missed=expected - len(hits),
        duplicated=sum(1 for count in hits.values() if count > 1),
        first=times[0],
        last=times[-1],
        gaps=largest,
    )


def tally(runs: list[Run]) -> str:
    if not runs:
        return "none"
    counts = Counter(run.outcome for run in runs)
    return ", ".join(f"{outcome} {counts[outcome]}" for outcome in sorted(counts))


def stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M")


def render(runs: list[Run], source: Path) -> str:
    scheduled = [run for run in runs if run.event == SCHEDULE_EVENT]
    manual = [run for run in runs if run.event == MANUAL_EVENT]
    other = len(runs) - len(scheduled) - len(manual)
    summary = summarize_schedule(scheduled)
    lines = ["App availability schedule report (UTC)", f"Source: {source}"]
    if summary.scheduled == 0:
        lines.append("Scheduled runs: 0 (no slots to evaluate)")
    else:
        lines += [
            f"Scheduled runs: {summary.scheduled}",
            f"Scheduled run window: {stamp(summary.first)} to {stamp(summary.last)}",
            f"Expected six-hourly slots: {summary.expected}",
            f"Missed slots: {summary.missed}",
            f"Slots with two or more runs: {summary.duplicated}",
            f"Scheduled conclusions: {tally(scheduled)}",
        ]
        if summary.gaps:
            lines.append("Largest gaps between scheduled runs:")
            lines += [f"  {hours:.2f} h  {stamp(start)} -> {stamp(end)}"
                      for hours, start, end in summary.gaps]
        else:
            lines.append("Largest gaps between scheduled runs: none (single run)")
    lines.append(f"Manual runs ({MANUAL_EVENT}): {len(manual)}")
    lines.append(f"Manual conclusions: {tally(manual)}")
    if other:
        lines.append(f"Other events excluded from both counts: {other}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs_json", type=Path, help="JSON file printed by gh run list")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.runs_json.read_text(encoding="utf-8"))
        runs = parse_runs(data)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, MalformedInput) as error:
        print(f"error: {args.runs_json}: {error}", file=sys.stderr)
        return EXIT_MALFORMED
    print(render(runs, args.runs_json))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
