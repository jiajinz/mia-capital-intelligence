"""admitted_elsewhere: a candidate whose exact bytes are already admitted in another series (AGENTS.md, D002)."""
import copy
import json
from pathlib import Path

import jsonschema
import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "discovery_catalog.schema.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "data" / "discovery" / "catalog.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=jsonschema.FormatChecker())


def test_catalog_validates_against_schema():
    assert list(VALIDATOR.iter_errors(CATALOG)) == []


def test_traffic_documents_are_admitted_elsewhere_not_not_included():
    traffic = [d for d in CATALOG["documents"] if d["series"] == "traffic_monthly"]
    assert traffic, "expected traffic documents in the catalog"
    for doc in traffic:
        assert doc["dataset_status"] == "admitted_elsewhere"
        assert doc["admitted_series"] == "traffic_monthly"


def test_admitted_elsewhere_requires_admitted_series():
    doc = copy.deepcopy(CATALOG["documents"][0])
    doc["dataset_status"] = "admitted_elsewhere"
    doc.pop("admitted_series", None)
    errors = list(VALIDATOR.iter_errors({"schema_version": CATALOG["schema_version"], "documents": [doc],
                                         "locations": [], "events": []}))
    assert errors, "admitted_elsewhere without admitted_series must be rejected"


def test_admitted_series_is_rejected_for_other_statuses():
    doc = copy.deepcopy(CATALOG["documents"][0])
    doc["dataset_status"] = "not_included"
    doc["admitted_series"] = "traffic_monthly"
    errors = list(VALIDATOR.iter_errors({"schema_version": CATALOG["schema_version"], "documents": [doc],
                                         "locations": [], "events": []}))
    assert errors, "admitted_series must only accompany admitted_elsewhere"


def test_new_candidate_with_admitted_bytes_is_recorded_as_admitted_elsewhere():
    from datetime import datetime, timezone
    from mia_capital_intelligence.discovery_catalog import observe
    from mia_capital_intelligence.discovery_sources import PDFIdentity, ReportLink, TRAFFIC, TRAFFIC_INDEX  # noqa: F401
    link = ReportLink(url="https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/x.pdf", series=TRAFFIC,
                      matter_id=None, title="Jan", source_page=TRAFFIC_INDEX, link_text="Jan")
    identity = PDFIdentity(sha256="c" * 64, size_bytes=1, page_count=1, period_start="2025-01-01",
                           period_end="2025-01-31", period_evidence="MONTH ENDED: JANUARY 31, 2025", period_pdf_page=1,
                           processing_status="candidate")
    when = datetime(2026, 11, 22, tzinfo=timezone.utc)
    admitted_catalog = {"schema_version": 1, "documents": [], "locations": [], "events": []}
    observe(admitted_catalog, link, identity, {}, when, admitted={"c" * 64: "traffic_monthly"})
    doc = admitted_catalog["documents"][0]
    assert doc["dataset_status"] == "admitted_elsewhere" and doc["admitted_series"] == "traffic_monthly"
    plain = {"schema_version": 1, "documents": [], "locations": [], "events": []}
    observe(plain, link, identity, {}, when)
    assert plain["documents"][0]["dataset_status"] == "not_included"
    assert "admitted_series" not in plain["documents"][0]
