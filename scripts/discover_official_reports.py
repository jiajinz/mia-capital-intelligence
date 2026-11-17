"""Check official indexes and write a reviewable candidate bundle to a temporary folder."""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mia_capital_intelligence.discovery_catalog import read_catalog
from mia_capital_intelligence.discovery_scan import scan
from mia_capital_intelligence.discovery_sources import OfficialClient


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("tmp/discovery-run"))
    parser.add_argument("--previous-catalog", type=Path)
    parser.add_argument("--max-new-documents", type=int, default=15)
    parser.add_argument("--full-hash-check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    # Runtime files and original PDFs must stay outside tracked inputs.
    if output != (root / "tmp").resolve() and (root / "tmp").resolve() not in output.parents:
        parser.error("--output must be a directory below the repository's ignored tmp directory")
    report = scan(root, output, client=OfficialClient(), when=datetime.now(timezone.utc),
                  previous=read_catalog(args.previous_catalog) if args.previous_catalog else None,
                  max_new_documents=args.max_new_documents, full_hash_check=args.full_hash_check)
    print(json.dumps({key: report[key] for key in ("status", "checked_documents", "unchanged_documents", "new_events", "deferred_documents")}))
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write((output / "summary.md").read_text())
    # Partial runs still yield safe candidates; a failing exit makes coverage problems visible.
    return 1 if report["errors"] or report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
