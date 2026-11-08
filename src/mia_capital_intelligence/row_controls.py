"""Pinned Exhibit B row controls used by the Stage 0 audit."""

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProfileRow:
    """One project token and its associated whole-dollar estimate."""

    project_id: str
    amount_usd: int | None


def load_page_controls(
    path: Path, *, matter_id: str, source_sha256: str, pdf_page: int
) -> list[ProfileRow]:
    """Load ordered controls and reject a missing page or different source version."""
    with path.open(encoding="utf-8", newline="") as stream:
        selected = [
            row for row in csv.DictReader(stream)
            if row["matter_id"] == matter_id and int(row["pdf_page"]) == pdf_page
        ]
    if not selected:
        raise ValueError(f"{matter_id} p.{pdf_page}: missing row controls")
    for ordinal, row in enumerate(selected, 1):
        if (
            row["source_sha256"] != source_sha256
            or row["exhibit"] != "B"
            or row["printed_page"] != f"MDC{pdf_page:03}"
            or int(row["row_ordinal"]) != ordinal
        ):
            raise ValueError(f"{matter_id} p.{pdf_page}: row control provenance differs")
    return [ProfileRow(row["project_id"], int(row["amount_usd"])) for row in selected]


def validate_page_rows(
    actual: list[ProfileRow], expected: list[ProfileRow], *, context: str
) -> None:
    """Require every ordered ID/amount pair to match the independent control."""
    if len(actual) != len(expected):
        raise ValueError(f"{context}: expected {len(expected)} rows, found {len(actual)}")
    for ordinal, (observed, control) in enumerate(zip(actual, expected, strict=True), 1):
        if observed != control:
            raise ValueError(
                f"{context} row {ordinal}: expected {control}, found {observed}"
            )
