"""Reconcile manually transcribed study evidence; never load it into the public registry."""

import argparse
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ("adopted_budget_usd", "approved_budget_usd", "prior_expenditures_usd",
           "monthly_expenditures_usd", "cumulative_expenditures_usd")
CONTRACTS = {"A19-MDAD-02", "A19-MDAD-01", "E20-MDAD-03", "MDAD-CIP-V009A"}


def amount(raw: str) -> Decimal:
    if not re.fullmatch(r"(?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2}", raw):
        raise ValueError(f"Unresolved or malformed financial amount: {raw}")
    return Decimal(raw.replace(",", ""))


def check_study(study: dict, pdf_dir: Path | None = None) -> list[dict]:
    """Check row/column arithmetic, summary agreement, identity and consecutive roll-forward."""
    results, previous = [], None
    if [source["report_month_label"] for source in study["sources"]] != ["2026-07", "2026-08", "2026-09"]:
        raise ValueError("Study requires the three consecutive reported months in order")
    for source in study["sources"]:
        if pdf_dir is not None:
            contents = (pdf_dir / f"{source['matter_id']}.pdf").read_bytes()
            if len(contents) != source["size_bytes"] or hashlib.sha256(contents).hexdigest() != source["sha256"]:
                raise ValueError("Study PDF identity mismatch")
        records = source["records"]
        if len(records) != 4 or {row["contract_id"] for row in records} != CONTRACTS:
            raise ValueError("Missing, duplicate or unexpected study contract")
        if [row["row_ordinal"] for row in records] != [1, 2, 3, 4]:
            raise ValueError("Financial row order is incomplete")
        totals = {metric: Decimal(0) for metric in METRICS}
        current = {}
        for row in records:
            contract = row["contract_id"]
            expected_raw = "E20-MDAD--03" if contract == "E20-MDAD-03" else contract
            if row["contract_raw_visual"] != expected_raw:
                raise ValueError("Unreviewed contract alias")
            values = {}
            for metric in METRICS:
                raw = row["raw_cells_visual"][metric]
                if raw == "-":
                    if metric != "monthly_expenditures_usd" or not row["dash_resolution"] or row["summary_expenditures"][metric] != "0.00":
                        raise ValueError("Dash has no explicit summary zero evidence")
                    raw = row["summary_expenditures"][metric]
                values[metric] = amount(raw)
                totals[metric] += values[metric]
            prior, monthly, cumulative = (values[metric] for metric in METRICS[2:])
            if prior + monthly != cumulative:
                raise ValueError("Prior plus monthly does not equal cumulative")
            if any(values[metric] != amount(row["summary_expenditures"][metric]) for metric in METRICS[2:]):
                raise ValueError("Financial and summary exhibits disagree")
            if previous and previous[contract] != prior:
                raise ValueError("Consecutive contract roll-forward does not reconcile")
            current[contract] = cumulative
        if any(totals[metric] != amount(source["printed_totals"][metric]) for metric in METRICS):
            raise ValueError("Printed financial column total does not reconcile")
        results.append({"month": source["report_month_label"], "contracts": 4,
                        "column_totals": {key: str(value) for key, value in totals.items()}})
        previous = current
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, help="Optional directory containing all three matter-ID PDFs")
    args = parser.parse_args()
    evidence = json.loads((ROOT / "docs/research/financial_snapshots.json").read_text())
    print(json.dumps(check_study(evidence, args.pdf_dir), indent=2))
