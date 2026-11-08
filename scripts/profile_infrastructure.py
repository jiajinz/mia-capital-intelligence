"""Reproduce Stage 0 page totals and raw exact-ID overlaps for two pinned PDFs."""

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pdfplumber

from mia_capital_intelligence.row_controls import (
    ProfileRow,
    load_page_controls,
    validate_page_rows,
)
from mia_capital_intelligence.source_identity import verify_pdf

ROOT = Path(__file__).resolve().parents[1]
PROJECT_TOKEN = re.compile(r"(?:[A-Z]{1,2}\d{3}[A-Z]{1,2}(?:[-.][A-Z0-9]+)*|TBD-\d+)")
USD_WHOLE = re.compile(r"\$?\d{1,3}(?:,\d{3})*")

# ID column bands in PDF points for A and B, measured on the pinned pages.
ID_BANDS = {"260526": ((21, 60), (39, 92)), "261402": ((33, 78), (50, 91))}


def profile(source: dict[str, Any], raw: Path) -> list[set[str]]:
    """Print page counts and amount subtotals, then return exhibit token sets."""
    matter = source["matter_id"]
    path = raw / f"{matter}.pdf"
    verify_pdf(path, expected_size=source["size_bytes"], expected_sha256=source["sha256"])
    exhibit_ids = []
    messages = []
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) != source["page_count"]:
            raise ValueError(f"{matter}: unexpected PDF page count")
        for exhibit_index, (exhibit, (id_left, id_right)) in enumerate(
            zip(source["tables"], ID_BANDS[matter], strict=True)
        ):
            tokens = Counter()
            for number in exhibit["pdf_pages"]:
                page = pdf.pages[number - 1]
                table = page.find_table()
                if table is None:
                    raise ValueError(f"{matter} p.{number}: table grid missing")
                grid_tokens = Counter(
                    row[0].split()[0] for row in table.extract()
                    if row[0] and row[0] not in {
                        "Project", "UNFUNDED PROJECTS", "PROJECTS IN THE PIPELINE"
                    }
                )
                anchors = [
                    word for word in page.extract_words()
                    if id_left - 1 <= word["x0"] and word["x1"] <= id_right
                    and PROJECT_TOKEN.fullmatch(word["text"])
                ]
                page_tokens = Counter(word["text"] for word in anchors)
                if page_tokens != grid_tokens:
                    raise ValueError(f"{matter} p.{number}: ID grid and coordinate counts differ")
                tokens.update(page_tokens)
                estimate_column = 2 if matter == "260526" else 3
                left, _, right, _ = table.columns[estimate_column].bbox
                subtotal = 0  # Exact integers for the reported whole-dollar cells.
                missing = 0
                page_rows = []
                for word in anchors:
                    band = page.crop((left, word["top"] - 1, right, word["bottom"] + 1))
                    raw_amount = re.sub(r"\s+", "", band.extract_text() or "")
                    if raw_amount == "-":
                        missing += 1
                        amount = None
                    elif USD_WHOLE.fullmatch(raw_amount):
                        amount = int(raw_amount.replace(",", "").lstrip("$"))
                        subtotal += amount
                    else:
                        raise ValueError(f"{matter} p.{number} {word['text']}: {raw_amount!r}")
                    page_rows.append(ProfileRow(word["text"], amount))
                if exhibit_index == 1:
                    expected = load_page_controls(
                        ROOT / "data/audit/exhibit_b_row_controls.csv",
                        matter_id=matter, source_sha256=source["sha256"], pdf_page=number,
                    )
                    validate_page_rows(page_rows, expected, context=f"{matter} B p.{number}")
                messages.append(
                    f"{matter} p.{number}: {len(anchors)} rows, ${subtotal:,}, {missing} dash(es)"
                )
            duplicates = sorted(key for key, count in tokens.items() if count > 1)
            if duplicates:
                raise ValueError(f"{matter} {exhibit['label']}: duplicate ID tokens {duplicates}")
            exhibit_ids.append(set(tokens))
    print("\n".join(messages))
    return exhibit_ids


def main() -> None:
    """Run the audit against repository-local source originals."""
    data = ROOT / "data"
    inventory = json.loads((data / "source_inventory.json").read_text(encoding="utf-8"))
    sources = {row["matter_id"]: row for row in inventory["sources"]}
    old_a, old_b = profile(sources["260526"], data / "raw")
    new_a, new_b = profile(sources["261402"], data / "raw")
    for exhibit, old, new in (("A", old_a, new_a), ("B", old_b, new_b)):
        print(f"Exhibit {exhibit}: {len(old & new)} exact overlaps, "
              f"{len(old - new)} earlier-only, {len(new - old)} later-only")
    print(f"261402 cross-exhibit overlaps: {sorted(new_a & new_b)}")


if __name__ == "__main__":
    main()
