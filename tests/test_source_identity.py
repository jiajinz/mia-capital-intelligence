import json
import re
from datetime import date, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

from mia_capital_intelligence.source_identity import verify_pdf

INVENTORY = Path(__file__).resolve().parents[1] / "data" / "source_inventory.json"
SOURCES = json.loads(INVENTORY.read_text(encoding="utf-8"))["sources"]


def test_inventory_has_three_distinct_sources() -> None:
    assert sorted(source["matter_id"] for source in SOURCES) == [
        "260526", "261400", "261402"
    ]
    assert len({source["sha256"] for source in SOURCES}) == len(SOURCES)


@pytest.mark.parametrize("source", SOURCES, ids=[row["matter_id"] for row in SOURCES])
def test_inventory_metadata(source: dict[str, Any]) -> None:
    pdf_url = urlparse(source["url"])
    matter_url = urlparse(source["matter_url"])
    assert pdf_url.scheme == matter_url.scheme == "https"
    assert pdf_url.hostname == matter_url.hostname == "www.miamidade.gov"
    assert pdf_url.path.endswith(f"/Y2026/{source['matter_id']}.pdf")
    assert parse_qs(matter_url.query)["matter"] == [source["matter_id"]]
    assert source["http_status"] == 200
    assert source["verification_status"] == "identity_and_bytes_verified"
    assert source["size_bytes"] > 0
    assert re.fullmatch(r"[0-9a-f]{64}", source["sha256"])

    start = date.fromisoformat(source["period_start"])
    end = date.fromisoformat(source["period_end"])
    accepted = date.fromisoformat(source["accepted_date"])
    assert start <= end < accepted
    for field in ("memo_date", "introduced_date"):
        assert date.fromisoformat(source[field]) <= accepted

    for table in source["tables"]:
        pages = table["pdf_pages"]
        assert table["label"] and pages
        assert pages == sorted(set(pages))
        assert 1 <= min(pages) <= max(pages) <= source["page_count"]
        assert len(pages) == len(table["printed_labels"])


def test_infrastructure_coverage_is_adjacent() -> None:
    first, second = sorted(
        (source for source in SOURCES if source["series"] == "infrastructure_241354"),
        key=lambda source: source["period_start"],
    )
    assert first["reporting_basis"] == second["reporting_basis"] == "explicit_memo_period"
    assert date.fromisoformat(first["period_end"]) + timedelta(days=1) == date.fromisoformat(
        second["period_start"]
    )


def test_verify_pdf_matches_expected_bytes(tmp_path: Path) -> None:
    fixture = b"%PDF-1.7\nsynthetic test payload\n"
    path = tmp_path / "fixture.pdf"
    path.write_bytes(fixture)
    verify_pdf(path, expected_size=len(fixture), expected_sha256=sha256(fixture).hexdigest())


@pytest.mark.parametrize(
    ("body", "size_delta", "message"),
    [
        (b"<html>server error</html>", 0, "PDF signature"),
        (b"%PDF-1.7\nfixture\n", 1, "byte count"),
        (b"%PDF-1.7\nfixture\n", 0, "SHA-256"),
    ],
)
def test_verify_pdf_rejects_unexpected_bytes(
    tmp_path: Path, body: bytes, size_delta: int, message: str
) -> None:
    path = tmp_path / "fixture.pdf"
    path.write_bytes(body)
    with pytest.raises(ValueError, match=message):
        verify_pdf(path, expected_size=len(body) + size_delta, expected_sha256="0" * 64)
