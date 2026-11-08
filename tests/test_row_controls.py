import csv
from pathlib import Path

import pytest

from mia_capital_intelligence.row_controls import (
    ProfileRow,
    load_page_controls,
    validate_page_rows,
)

ROWS = [ProfileRow("T180B", 914627764), ProfileRow("T180D", 163567943)]


@pytest.mark.parametrize(
    "actual",
    [
        ROWS[:1],
        [ProfileRow("T180B", 163567943), ProfileRow("T180D", 914627764)],
        [ProfileRow("T180B", 914627765), ROWS[1]],
        [ROWS[0], ROWS[0]],
        [ProfileRow("T180B", None), ROWS[1]],
        list(reversed(ROWS)),
    ],
    ids=["omitted-row", "same-total-swap", "wrong-cell", "duplicate", "missing", "reordered"],
)
def test_row_controls_reject_corruption(actual: list[ProfileRow]) -> None:
    with pytest.raises(ValueError, match="test page"):
        validate_page_rows(actual, ROWS, context="test page")


def test_row_controls_accept_exact_id_and_amounts() -> None:
    validate_page_rows(ROWS, ROWS.copy(), context="test page")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_sha256", "wrong"),
        ("exhibit", "A"),
        ("printed_page", "MDC012"),
        ("row_ordinal", "2"),
    ],
)
def test_control_provenance_is_required(tmp_path: Path, field: str, value: str) -> None:
    control = {
        "matter_id": "260526", "source_sha256": "verified", "exhibit": "B",
        "pdf_page": "11", "printed_page": "MDC011", "row_ordinal": "1",
        "project_id": "T180B", "amount_usd": "914627764",
    }
    control[field] = value
    path = tmp_path / "controls.csv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=control)
        writer.writeheader()
        writer.writerow(control)
    with pytest.raises(ValueError, match="provenance"):
        load_page_controls(path, matter_id="260526", source_sha256="verified", pdf_page=11)


def test_missing_control_page_fails(tmp_path: Path) -> None:
    path = tmp_path / "controls.csv"
    path.write_text("matter_id,pdf_page\n")
    with pytest.raises(ValueError, match="missing row controls"):
        load_page_controls(path, matter_id="260526", source_sha256="verified", pdf_page=11)
