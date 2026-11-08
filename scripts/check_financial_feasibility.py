"""Reconcile manually transcribed study evidence; never load it into the public registry."""

import argparse
import hashlib
import json
import re
from contextlib import closing
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ("adopted_budget_usd", "approved_budget_usd", "prior_expenditures_usd",
           "monthly_expenditures_usd", "cumulative_expenditures_usd")
CONTRACTS = {"A19-MDAD-02", "A19-MDAD-01", "E20-MDAD-03", "MDAD-CIP-V009A"}
ISSUES = {
    "2026-07": ("261147", 28, (19, 20), "July 2026",
                "355c1d4d130e9b8a0eeed6f160131fd6bc8db4b10ba5e75818a60a849bc02a62"),
    "2026-08": ("261399", 29, (20, 21), "August 2026",
                "c62074ae4fdccda48bc716a399d585d8246e8d36a929633ef3afefe6c5505bbe"),
    "2026-09": ("261400", 30, (21, 22), "September 2026",
                "ae45ec3eeaf1f54df04ad2255ed9ec3c0f3f647d3b2570b39272ff75efe9f9ae"),
}
HEADINGS = dict(zip(METRICS, (
    "FY 2025-2026 Adopted Budget Amount", "Current Approved Budget Amount", "Prior Expenditures",
    "Current Month Expenditures", "Cumulative Expenditures to Date",
), strict=True))
MONEY = r"(?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2}"
SUMMARY_ROW = re.compile(
    rf"([\w-]+) (.*?) Prior Expenditures: \$({MONEY}) "
    rf"Current Month Expenditures: \$({MONEY}) Cumulative Expenditures to Date: \$({MONEY})\b"
)


def page_text(pdf, number: int) -> str:
    with closing(pdf[number - 1]) as page, closing(page.get_textpage()) as text_page:
        # July's PDF font maps its printed hyphen to U+0372.
        return text_page.get_text_range().replace("\r", "").replace("\u0372", "-")


def read_pdf_controls(source: dict, pdf_dir: Path) -> tuple[list[dict], dict[str, dict], dict]:
    """Read ordered financial cells and contract-local summary fields from pinned PDF pages."""
    import pypdfium2 as pdfium

    matter, financial_page, summary_pages, month_name, digest = ISSUES[source["report_month_label"]]
    contents = (pdf_dir / f"{matter}.pdf").read_bytes()
    if len(contents) != source["size_bytes"] or hashlib.sha256(contents).hexdigest() != digest:
        raise ValueError("Study PDF identity mismatch")
    with pdfium.PdfDocument(contents) as pdf:
        if len(pdf) != source["page_count"]:
            raise ValueError("Study PDF page count mismatch")
        financial = page_text(pdf, financial_page)
        summaries = {number: page_text(pdf, number) for number in summary_pages}
    blocks = re.split(r"(?m)^\s*(?=(?:A19-MDAD-0[12]|E20-MDAD--03|MDAD-CIP-V009A)\b|TOTAL\b)", financial)
    header = " ".join(blocks[0].split())
    expected = " ".join(HEADINGS.values())
    if len(blocks) != 6 or expected not in header or not financial.strip().endswith(f"MDC{financial_page:03}"):
        raise ValueError("Unexpected financial PDF layout or monetary heading order")
    rows = []
    for ordinal, block in enumerate(blocks[1:5], 1):
        raw_id, _, body = " ".join(block.split()).partition(" ")
        match = re.fullmatch(r"(.+?) Awarded \d{2}/\d{2}/\d{2} (.+)", body)
        if not match:
            raise ValueError("Unexpected financial PDF row layout")
        description, values = match.groups()
        rows.append({"row_ordinal": ordinal, "contract_raw_visual": raw_id,
                     "description_raw_visual": description,
                     "raw_cells_visual": dict(zip(METRICS, values.split()[:5], strict=True))})
    totals = dict(zip(METRICS, blocks[5].split()[1:6], strict=True))
    summary_rows = {}
    for number, raw_page in summaries.items():
        if not raw_page.strip().endswith(f"MDC{number:03}") or f"Summary of Changes {month_name}" not in " ".join(raw_page.split()):
            raise ValueError("Unexpected summary PDF page or reported month")
        blocks = re.split(r"(?m)^Yes Contract No\.\s*", raw_page)[1:]
        for ordinal, block in enumerate(blocks, 1):
            match = SUMMARY_ROW.match(" ".join(block.split()))
            if not match or match[1] in summary_rows:
                raise ValueError("Unexpected or duplicate contract summary row")
            summary_rows[match[1]] = {
                "summary_pdf_page": number, "summary_row_ordinal": ordinal,
                "summary_contract_raw": match[1], "summary_description_raw": match[2],
                "summary_expenditures": dict(zip(METRICS[2:], match.groups()[2:], strict=True)),
            }
    if set(summary_rows) != CONTRACTS:
        raise ValueError("Incomplete financial summary coverage")
    return rows, summary_rows, totals


def amount(raw: str) -> Decimal:
    if not re.fullmatch(MONEY, raw):
        raise ValueError(f"Unresolved or malformed financial amount: {raw}")
    return Decimal(raw.replace(",", ""))


def check_study(study: dict, pdf_dir: Path | None = None) -> list[dict]:
    """Check row/column arithmetic, summary agreement, identity and consecutive roll-forward."""
    results, previous = [], None
    if [source["report_month_label"] for source in study["sources"]] != list(ISSUES):
        raise ValueError("Study requires the three consecutive reported months in order")
    for source in study["sources"]:
        matter, page, summary_pages, _, digest = ISSUES[source["report_month_label"]]
        if (source["matter_id"], source["sha256"], source["financial_pdf_page"], source["printed_page"],
                source["exhibit"], tuple(source["summary_pdf_pages"])) != (
                matter, digest, page, f"MDC{page:03}", "B", summary_pages):
            raise ValueError("Study issue or financial page binding mismatch")
        if source["columns"] != HEADINGS:
            raise ValueError("Study financial heading binding mismatch")
        records = source["records"]
        if len(records) != 4 or {row["contract_id"] for row in records} != CONTRACTS:
            raise ValueError("Missing, duplicate or unexpected study contract")
        if [row["row_ordinal"] for row in records] != [1, 2, 3, 4]:
            raise ValueError("Financial row order is incomplete")
        if pdf_dir is not None:
            financial, summaries, printed_totals = read_pdf_controls(source, pdf_dir)
            for row, original in zip(records, financial, strict=True):
                if any(row.get(field) != value for field, value in original.items()):
                    raise ValueError(f"Financial PDF row binding mismatch for {matter} row {original['row_ordinal']}")
                if any(row.get(field) != value for field, value in summaries[row["contract_id"]].items()):
                    raise ValueError(f"Summary PDF row binding mismatch for {matter} {row['contract_id']}")
            if source["printed_totals"] != printed_totals:
                raise ValueError("Printed PDF total cells disagree with study evidence")
        totals = {metric: Decimal(0) for metric in METRICS}
        current = {}
        for row in records:
            contract = row["contract_id"]
            expected_raw = "E20-MDAD--03" if contract == "E20-MDAD-03" else contract
            if row["contract_raw_visual"] != expected_raw:
                raise ValueError("Unreviewed contract alias")
            if row["summary_contract_raw"] != contract or row["summary_pdf_page"] not in summary_pages:
                raise ValueError("Unexpected summary contract or page")
            if contract == "A19-MDAD-01" and row.get("airport_attribution") is not None:
                raise ValueError("A19-MDAD-01 airport attribution remains unresolved")
            has_dash = row["raw_cells_visual"]["monthly_expenditures_usd"] == "-"
            if row["dash_resolution"] != ("summary_explicit_zero" if has_dash else None):
                raise ValueError("Unsupported dash resolution")
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
    parser.add_argument("--pdf-dir", type=Path, help="Verify source bindings against three pinned matter-ID PDFs")
    args = parser.parse_args()
    evidence = json.loads((ROOT / "docs/research/financial_snapshots.json").read_text())
    print(json.dumps({
        "verification": "study PDF bindings and arithmetic" if args.pdf_dir else "study arithmetic and static pins only",
        "months": check_study(evidence, args.pdf_dir),
    }, indent=2))
