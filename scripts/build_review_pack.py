"""Build the independent review pack for one candidate monthly traffic admission.

The pack holds the COMBINED TOTALS rows of one candidate PDF, the deterministic checks run on
them, source digests, page references, and the diff against the admitted dataset for the same
period. It refuses to write when any check fails, when no candidate matches the period, or when
the output would land inside the repository. It never writes into the candidate folder.

Usage:
  build_review_pack.py --folder DIR --period YYYY-MM --out NEW_FILE [--admitted ADMITTED.json]

Without --admitted, the prior-year and CYTD checks fail closed, so no pack is written.
Exit code 2 means refused.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mia_capital_intelligence import traffic_pilot as traffic

PACK_VERSION = "admission-review-pack-1"
SERIES = "traffic_monthly"
MARKET = "COMBINED TOTALS"
SCOPE = ("PASSENGERS", "TOTAL CARGO-TONS")
TRANSFORM = "Printed monthly TOTAL; remove grouping commas; parse integer"
PERIOD = re.compile(r"(\d{4})-(0[1-9]|1[0-2])")
ENDED = re.compile(r"MONTH ENDED: ([A-Z]+) (\d{1,2}), (\d{4})")
MONTHS = {name.upper(): number for number, name in enumerate(calendar.month_name) if number}


class ReviewRefused(ValueError):
    """The pack cannot be written: a check failed or the inputs cannot support a review."""


class Admitted(NamedTuple):
    name: str
    sha256: str
    dataset_version: str | None
    revision_rule: str | None
    rows: dict[tuple[str, str, str], dict]


def tolerance(measure: str) -> int:
    # Reported tons may differ by one ton from printed sums (rounding), as in traffic_pilot.
    return int(traffic.MEASURES[measure] == "reported tons")


def parse_period(text: str) -> tuple[int, int]:
    match = PERIOD.fullmatch(text)
    if not match:
        raise ReviewRefused(f"period must be YYYY-MM, got {text!r}")
    return int(match[1]), int(match[2])


def load_admitted(path: Path) -> Admitted:
    body = path.read_bytes()
    data = json.loads(body)
    rows: dict[tuple[str, str, str], dict] = {}
    for row in data["rows"]:
        key = (row["period"], row["market"], row["measure"])
        if key in rows:
            raise ReviewRefused(f"admitted file repeats {key}")
        rows[key] = row
    return Admitted(path.name, hashlib.sha256(body).hexdigest(), data.get("dataset_version"),
                    data.get("revision_rule"), rows)


def check(check_id: str, scope: str, expected: object, observed: object, passed: bool) -> dict:
    return {"id": check_id, "scope": scope, "expected": expected, "observed": observed, "pass": bool(passed)}


def read_candidate(folder: Path, period: str) -> tuple[dict, list[dict]]:
    """Return the one candidate PDF that yields the period, plus every file that did not."""
    if not folder.is_dir():
        raise ReviewRefused(f"candidate folder not found: {folder.name}")
    matches: list[dict] = []
    ignored: list[dict] = []
    for path in sorted(folder.iterdir()):
        if not (path.is_file() and path.suffix.lower() == ".pdf"):
            continue
        body = path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        try:
            rows = traffic.read_page(body, period)
        except Exception as error:  # A file that fails extraction is excluded and listed, never silently used.
            ignored.append({"file": path.name, "sha256": digest, "reason": f"{type(error).__name__}: {error}"})
            continue
        matches.append({"file": path.name, "sha256": digest, "rows": rows})
    if not matches:
        reasons = "; ".join(f"{item['file']}: {item['reason']}" for item in ignored) or "no PDF files"
        raise ReviewRefused(f"no candidate PDF yields {period} traffic rows ({reasons})")
    digests = {match["sha256"] for match in matches}
    if len(digests) > 1:
        names = ", ".join(sorted(match["file"] for match in matches))
        raise ReviewRefused(f"{len(digests)} different PDFs yield {period} ({names}); keep one candidate")
    first, *duplicates = sorted(matches, key=lambda match: match["file"])
    for duplicate in duplicates:
        ignored.append({"file": duplicate["file"], "sha256": duplicate["sha256"],
                        "reason": f"duplicate of {first['file']}"})
    rows = [row for row in first["rows"] if row["market"] == MARKET and row["measure"] in SCOPE]
    rows.sort(key=lambda row: SCOPE.index(row["measure"]))
    if [row["measure"] for row in rows] != list(SCOPE):
        raise ReviewRefused(f"{period}: COMBINED TOTALS rows for {', '.join(SCOPE)} not all present")
    candidate = {"file": first["file"], "sha256": first["sha256"], "rows": rows}
    return candidate, sorted(ignored, key=lambda item: item["file"])


def page_checks(period: str, rows: list[dict], admitted: Admitted | None) -> list[dict]:
    year, month = parse_period(period)
    printed = ENDED.fullmatch(rows[0]["period_evidence"])
    if not printed:
        raise ReviewRefused(f"{period}: printed month-end line not recognised")
    observed_period = f"{int(printed[3]):04}-{MONTHS[printed[1]]:02}"
    printed_day = int(printed[2])
    last_day = calendar.monthrange(year, month)[1]
    rule = admitted.revision_rule if admitted else "no admitted reference supplied"
    return [
        check("period_evidence", "page", period, observed_period, observed_period == period),
        check("printed_month_end", "page", last_day, printed_day, printed_day == last_day),
        check("two_vintage_rule", "page", "two_vintages", rule, rule == "two_vintages"),
    ]


def cytd_check(period: str, row: dict, admitted: Admitted | None, scope: str) -> dict:
    year, month = parse_period(period)
    measure = row["measure"]
    observed = traffic.cell_count(row["raw"]["cytd"])
    if month == 1:
        expected = row["value"]
    elif admitted is None:
        return check("cytd_rule", scope, "admitted reference required for earlier months", observed, False)
    else:
        earlier = [f"{year}-{k:02}" for k in range(1, month)]
        missing = [p for p in earlier if (p, MARKET, measure) not in admitted.rows]
        if missing:
            return check("cytd_rule", scope, f"admitted {earlier[0]} to {earlier[-1]}",
                         f"missing {', '.join(missing)}", False)
        expected = row["value"] + sum(admitted.rows[p, MARKET, measure]["value"] for p in earlier)
    return check("cytd_rule", scope, expected, observed, abs(observed - expected) <= tolerance(measure))


def prior_year_check(period: str, row: dict, admitted: Admitted | None, scope: str) -> dict:
    year, month = parse_period(period)
    observed = traffic.cell_count(row["raw"]["same_month_prior_year"])
    if admitted is None:
        return check("prior_year_same_month", scope, "admitted reference required", observed, False)
    prior_period = f"{year - 1}-{month:02}"
    prior = admitted.rows.get((prior_period, MARKET, row["measure"]))
    if prior is None:
        return check("prior_year_same_month", scope, f"admitted {prior_period}", observed, False)
    return check("prior_year_same_month", scope, prior["value"], observed, observed == prior["value"])


def measure_checks(period: str, row: dict, admitted: Admitted | None) -> list[dict]:
    scope = f"{MARKET} {row['measure']}"
    raw = row["raw"]
    deplaned = traffic.cell_count(raw["deplaned"])
    enplaned = traffic.cell_count(raw["enplaned"])
    reconciled = deplaned + enplaned
    return [
        check("deplaned_plus_enplaned_equals_total", scope, row["value"], reconciled,
              abs(row["value"] - reconciled) <= tolerance(row["measure"])),
        cytd_check(period, row, admitted, scope),
        prior_year_check(period, row, admitted, scope),
    ]


def diff_against_admitted(period: str, candidate: dict, admitted: Admitted | None) -> tuple[dict, list[dict]]:
    rows = candidate["rows"]
    if admitted is None:
        return {"status": "no_admitted_reference", "changes": [], "follow_up_requests": []}, []
    prior = {row["measure"]: admitted.rows.get((period, MARKET, row["measure"])) for row in rows}
    present = [item for item in prior.values() if item is not None]
    if not present:
        status = "new_period"
        admitted_source = None
    elif len(present) != len(rows):
        raise ReviewRefused(f"admitted file holds only part of {period}")
    else:
        digests = {item["source_sha256"] for item in present}
        if len(digests) != 1:
            raise ReviewRefused(f"admitted file mixes source digests for {period}")
        admitted_source = digests.pop()
        status = "unchanged_source" if admitted_source == candidate["sha256"] else "revised_source"
    changes, follow_up, checks = [], [], []
    for row in rows:
        before = prior[row["measure"]]
        if before is None:
            continue
        if status == "unchanged_source":
            checks.append(check("same_source_value", f"{MARKET} {row['measure']}", before["value"],
                                row["value"], before["value"] == row["value"]))
        if before["value"] != row["value"]:
            changes.append({"market": MARKET, "measure": row["measure"], "field": "value",
                            "before": before["value"], "after": row["value"],
                            "delta": row["value"] - before["value"]})
            follow_up.append(f"{period} {row['measure']}: admitted {before['value']} vs candidate "
                             f"{row['value']} from a different PDF; confirm the revision.")
    first_published = None
    if present:
        first_published = present[0].get("vintage", {}).get("first_published")
    diff = {
        "status": status,
        "admitted_file": admitted.name,
        "admitted_sha256": admitted.sha256,
        "admitted_source_sha256": admitted_source,
        "candidate_sha256": candidate["sha256"],
        "values_candidate": {row["measure"]: row["value"] for row in rows},
        "changes": changes,
        "first_published_retained": first_published,
        "follow_up_requests": follow_up,
    }
    return diff, checks


def row_record(row: dict, file_name: str) -> dict:
    return {
        "market": row["market"],
        "measure": row["measure"],
        "unit": row["unit"],
        "value": row["value"],
        "raw": dict(row["raw"]),
        "held_fields": list(row["held_fields"]),
        "month_end_note": row["month_end_note"],
        "residuals": dict(row["residuals"]),
        "page_reference": {
            "file": file_name,
            "page_index": row["pdf_page_index"],
            "row_label": row["measure"],
            "table_header": row["table_header"],
            "period_evidence": row["period_evidence"],
            "row_y": row["row_y"],
            "total_x": row["total_x"],
        },
    }


def build_pack(folder: Path, period: str, admitted_path: Path | None = None) -> dict:
    parse_period(period)
    admitted = load_admitted(admitted_path) if admitted_path else None
    candidate, ignored = read_candidate(folder, period)
    rows = candidate["rows"]
    checks = page_checks(period, rows, admitted)
    for row in rows:
        checks += measure_checks(period, row, admitted)
    diff, diff_checks = diff_against_admitted(period, candidate, admitted)
    checks += diff_checks
    failed = [item for item in checks if not item["pass"]]
    if failed:
        details = "; ".join(f"{item['scope']} {item['id']}: expected {item['expected']}, "
                            f"observed {item['observed']}" for item in failed)
        raise ReviewRefused(f"{period} blocked by {len(failed)} failed check(s): {details}")
    return {
        "pack_version": PACK_VERSION,
        "series": SERIES,
        "period": period,
        "scope": f"{MARKET}: {', '.join(SCOPE)}",
        "transform": TRANSFORM,
        "source_documents": [{"file": candidate["file"], "sha256": candidate["sha256"], "pages": 1,
                              "period_evidence": rows[0]["period_evidence"]}],
        "ignored_files": ignored,
        "admitted_reference": None if admitted is None else {
            "file": admitted.name, "sha256": admitted.sha256,
            "dataset_version": admitted.dataset_version, "revision_rule": admitted.revision_rule},
        "rows": [row_record(row, candidate["file"]) for row in rows],
        "checks": checks,
        "diff_against_admitted": diff,
    }


def write_pack(out: Path, pack: dict) -> None:
    target = out.resolve()
    common = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                            capture_output=True, text=True, check=True).stdout.strip()
    repository = Path(common).parent.resolve()
    if repository in (target, *target.parents):
        raise ReviewRefused("refusing to write inside the repository; choose a path outside it")
    if target.exists():
        raise ReviewRefused(f"output exists: {target.name}; choose a new file so a reviewed pack is not replaced")
    body = (json.dumps(pack, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
    with target.open("xb") as file:
        file.write(body)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--folder", type=Path, required=True, help="local folder holding candidate PDFs")
    parser.add_argument("--period", required=True, help="calendar month, YYYY-MM")
    parser.add_argument("--admitted", type=Path, default=None, help="admitted traffic JSON for cross-checks")
    parser.add_argument("--out", type=Path, required=True, help="new review-pack.json path outside the repository")
    args = parser.parse_args(argv)
    try:
        pack = build_pack(args.folder, args.period, args.admitted)
        write_pack(args.out, pack)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"REFUSED {args.period}: {error}", file=sys.stderr)
        return 2
    print(f"wrote review pack for {args.period}: {len(pack['checks'])} checks passed, "
          f"diff status {pack['diff_against_admitted']['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
