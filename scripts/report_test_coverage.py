"""Report separate line and branch percentages from coverage.py JSON output."""

import argparse
import json
import os
from pathlib import Path
from typing import Any


def measurement(covered: int, total: int, unit: str) -> str:
    if type(covered) is not int or type(total) is not int or not 0 <= covered <= total:
        raise ValueError(f"Invalid {unit} coverage counts")
    return f"{covered / total:.2%} ({covered}/{total} {unit})" if total else f"N/A (no {unit})"


def summary(report: dict[str, Any], label: str) -> str:
    if report.get("meta", {}).get("branch_coverage") is not True:
        raise ValueError("Coverage must be collected with branch measurement enabled")
    totals = report["totals"]
    lines = measurement(totals["covered_lines"], totals["num_statements"], "executable lines")
    branches = measurement(totals["covered_branches"], totals["num_branches"], "branch destinations")
    return (f"## Test coverage — {label}\n\n"
            f"- Line coverage: **{lines}**.\n"
            f"- Branch coverage: **{branches}**.\n"
            f"- Source files measured: {len(report['files'])}.\n\n"
            "The HTML report identifies unexecuted lines and branch destinations.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("tmp/coverage/coverage.json"))
    parser.add_argument("--output", type=Path, default=Path("tmp/coverage/summary.md"))
    parser.add_argument("--label", default="All runtime code")
    args = parser.parse_args()
    rendered = summary(json.loads(args.input.read_text()), args.label)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered)
    if destination := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(destination).open("a", encoding="utf-8") as stream:
            stream.write(rendered)


if __name__ == "__main__":
    main()
