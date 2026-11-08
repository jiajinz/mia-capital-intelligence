"""Independently check pinned Exhibit B rows using PDFium column text and positions."""

import json
from contextlib import closing
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium

from mia_capital_intelligence.row_controls import (
    ProfileRow,
    load_page_controls,
    validate_page_rows,
)
from mia_capital_intelligence.source_identity import verify_pdf

ROOT = Path(__file__).resolve().parents[1]
# PDF points, origin at lower left. Body tops exclude the printed table headings.
BANDS = {
    "260526": {"id": (39, 81), "amount": (305.22, 362.22), "body_top": 705},
    "261402": {"id": (50, 91), "amount": (357.72, 413.04), "body_top": 698},
}


def independent_rows(text: Any, matter_id: str) -> list[ProfileRow]:
    """Read every nonempty ID-column line, then bind its amount by vertical position."""
    band = BANDS[matter_id]
    left, right = band["id"]
    identifiers = text.get_text_bounded(left, 40, right, band["body_top"]).splitlines()
    rows = []
    for raw_id in identifiers:
        project_id = raw_id.strip()
        if not project_id:
            continue
        with closing(text.search(project_id, match_case=True, match_whole_word=True)) as search:
            occurrences = []
            while (match := search.get_next()) is not None:
                boxes = [text.get_charbox(i) for i in range(match[0], match[0] + match[1])]
                x0 = min(box[0] for box in boxes)
                x1 = max(box[2] for box in boxes)
                bottom = min(box[1] for box in boxes)
                top = max(box[3] for box in boxes)
                if left <= x0 and x1 <= right and 40 <= bottom <= top <= band["body_top"]:
                    full_id = text.get_text_bounded(left, bottom - 1, right, top + 1).strip()
                    if full_id == project_id:
                        occurrences.append((bottom, top))
        if len(occurrences) != 1:
            raise ValueError(f"{matter_id} {project_id}: expected one ID-column occurrence")
        bottom, top = occurrences[0]
        cost_left, cost_right = band["amount"]
        raw_cost = text.get_text_bounded(cost_left, bottom - 1, cost_right, top + 1)
        compact = "".join(raw_cost.split()).removeprefix("$").replace(",", "")
        rows.append(ProfileRow(project_id, int(compact)))
    return rows


def main() -> None:
    """Compare the second extractor against the checked-in row controls."""
    sources = json.loads((ROOT / "data/source_inventory.json").read_text())["sources"]
    for source in sources:
        matter = source["matter_id"]
        if matter not in BANDS:
            continue
        path = ROOT / f"data/raw/{matter}.pdf"
        verify_pdf(path, expected_size=source["size_bytes"], expected_sha256=source["sha256"])
        exhibit = source["tables"][1]
        with closing(pdfium.PdfDocument(path)) as document:
            for number in exhibit["pdf_pages"]:
                with closing(document[number - 1]) as page, closing(page.get_textpage()) as text:
                    rows = independent_rows(text, matter)
                expected = load_page_controls(
                    ROOT / "data/audit/exhibit_b_row_controls.csv",
                    matter_id=matter, source_sha256=source["sha256"], pdf_page=number,
                )
                validate_page_rows(rows, expected, context=f"PDFium {matter} B p.{number}")
                print(f"{matter} B p.{number}: {len(rows)} independent row controls matched")


if __name__ == "__main__":
    main()
