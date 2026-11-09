"""Reconcile the financial evidence and optionally verify pinned PDF source bindings."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mia_capital_intelligence.financial_sources import check_study


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, help="Verify source bindings against three pinned matter-ID PDFs")
    args = parser.parse_args()
    evidence = json.loads((ROOT / "data/financial/snapshots.v1.json").read_text())
    print(json.dumps({
        "verification": "study PDF bindings and arithmetic" if args.pdf_dir else "study arithmetic and static pins only",
        "months": check_study(evidence, args.pdf_dir),
    }, indent=2))
