"""Read-only Stage 1A CLI. Every view is produced by the same approval gate."""

import argparse
import json
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from mia_capital_intelligence.comparability import ROOT, evaluate_gate
from mia_capital_intelligence.source_records import load_exhibit_b

SECTIONS = (
    "candidates", "held_pairs", "approved_comparisons", "excluded_pairs",
    "unmatched_records", "validation_errors", "blocked_comparisons", "source_observations",
)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def load_review_bundle(path: Path) -> dict[str, Any]:
    """Read local decisions while rejecting duplicate JSON object fields."""
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)


def json_value(value: Any) -> str:
    """Serialize dates and decimal amounts without floating-point conversion."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, ".2f")
    raise TypeError(f"Unsupported audit value: {type(value).__name__}")


def serialize_report(report: dict[str, Any]) -> str:
    """Produce deterministic JSON with explicit decimal strings."""
    return json.dumps(report, default=json_value, sort_keys=True, indent=2) + "\n"


def select_view(
    report: dict[str, Any], *, section: str | None = None, project_id: str | None = None
) -> dict[str, Any]:
    """Select an already evaluated audit view, retaining its global validation state."""
    if section is not None and section not in SECTIONS:
        raise ValueError(f"Unknown audit section: {section}")
    selected = dict(report)
    if project_id is not None:
        for name in SECTIONS:
            if name != "validation_errors":
                selected[name] = [
                    row for row in report[name] if row.get("project_id") == project_id
                ]
        selected["selected_project_id"] = project_id
    if section is not None:
        return {name: selected[name] for name in (
            "contract_version", "review_schema_sha256", "review_bundle_sha256",
            "independence_disclosure", "summary", "validation_errors", section
        )}
    return selected


def main(argv: list[str] | None = None) -> int:
    """Validate local sources and decisions before querying or emitting any result."""
    parser = argparse.ArgumentParser(description="Independent MIA Exhibit B comparability audit")
    parser.add_argument("--reviews", type=Path, default=ROOT / "data/review_dispositions.json")
    parser.add_argument("--section", choices=SECTIONS)
    parser.add_argument("--project", help="Exact reported project token")
    args = parser.parse_args(argv)
    try:
        documents, records = load_exhibit_b(ROOT)
        bundle = load_review_bundle(args.reviews)
        report = evaluate_gate(documents, records, bundle)
    except (OSError, ValueError) as error:
        sys.stdout.write(serialize_report({
            "approved_comparisons": [],
            "validation_errors": [{"code": "input_failure", "location": str(args.reviews),
                                   "message": str(error)}],
        }))
        return 1
    sys.stdout.write(serialize_report(select_view(report, section=args.section, project_id=args.project)))
    return 0 if report["summary"]["input_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
