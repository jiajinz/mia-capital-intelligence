"""Load only the four controlled Exhibit B pages as source observations."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pdfplumber

from mia_capital_intelligence.comparability_model import (
    AmountObservation,
    SourceDocument,
    SourceRecord,
)
from mia_capital_intelligence.row_controls import ProfileRow, load_page_controls, validate_page_rows
from mia_capital_intelligence.source_identity import verify_pdf


def load_exhibit_b(root: Path) -> tuple[tuple[SourceDocument, SourceDocument], list[SourceRecord]]:
    """Verify pinned bytes and every controlled row before returning observations."""
    inventory = json.loads((root / "data/source_inventory.json").read_text(encoding="utf-8"))
    sources = {row["matter_id"]: row for row in inventory["sources"]}
    documents = []
    records = []
    for matter, caption in (
        ("260526", "FY 2024- 2025; for Period October 2025 - December 2025"),
        ("261402", "FY 2025- 2026"),
    ):
        source = sources[matter]
        exhibit = source["tables"][1]
        expected_pages = [11, 12] if matter == "260526" else [12, 13]
        if (exhibit["label"] != "Exhibit B - Capital Improvement Program"
                or exhibit["pdf_pages"] != expected_pages):
            raise ValueError(f"{matter}: unexpected Exhibit B identity")
        path = root / f"data/raw/{matter}.pdf"
        verify_pdf(path, expected_size=source["size_bytes"], expected_sha256=source["sha256"])
        document = SourceDocument(
            matter, source["sha256"], source["url"], source["title"],
            date.fromisoformat(source["period_start"]), date.fromisoformat(source["period_end"]),
            date.fromisoformat(source["memo_date"]), caption, tuple(exhibit["pdf_pages"]),
        )
        documents.append(document)
        with pdfplumber.open(path) as pdf:
            if len(pdf.pages) != source["page_count"]:
                raise ValueError(f"{matter}: PDF page count differs")
            for number in exhibit["pdf_pages"]:
                table = pdf.pages[number - 1].find_table()
                if table is None:
                    raise ValueError(f"{matter} p.{number}: table grid missing")
                cells = table.extract()
                cost_column = 2 if matter == "260526" else 3
                if "Total Estimated" not in cells[0][cost_column]:
                    raise ValueError(f"{matter} p.{number}: estimate header differs")
                page_records = []
                for ordinal, row in enumerate(cells[1:], 1):
                    if not row[0]:
                        raise ValueError(f"{matter} p.{number} row {ordinal}: missing ID cell")
                    project_id, _, merged_description = row[0].partition(" ")
                    description = row[1] if row[1] is not None else merged_description
                    raw_amount = row[cost_column]
                    if raw_amount is None:
                        raise ValueError(f"{matter} p.{number} row {ordinal}: missing estimate")
                    amount = int("".join(raw_amount.split()).removeprefix("$").replace(",", ""))
                    metric = AmountObservation(
                        Decimal(amount), raw_amount, cells[0][cost_column]
                    )
                    page_records.append(SourceRecord(
                        matter, source["sha256"], "B", number, ordinal, project_id,
                        description, {"total_estimated_cost_usd": metric},
                        tuple(table.rows[ordinal].bbox),
                    ))
                expected = load_page_controls(
                    root / "data/audit/exhibit_b_row_controls.csv", matter_id=matter,
                    source_sha256=source["sha256"], pdf_page=number,
                )
                validate_page_rows(
                    [ProfileRow(row.project_id, int(row.metrics["total_estimated_cost_usd"].value))
                     for row in page_records],
                    expected, context=f"{matter} B p.{number}",
                )
                records.extend(page_records)
    return (documents[0], documents[1]), records
