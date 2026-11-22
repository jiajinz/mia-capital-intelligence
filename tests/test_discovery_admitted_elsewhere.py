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


def test_index_builds_from_real_traffic_files_without_series_id_on_every_file():
    from mia_capital_intelligence.discovery_catalog import admitted_elsewhere_index
    index = admitted_elsewhere_index(ROOT)
    assert index, "expected admitted traffic hashes"
    assert set(index.values()) == {"traffic_monthly"}


def _candidate(sha: str, url: str = "https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/x.pdf"):
    from mia_capital_intelligence.discovery_sources import TRAFFIC, TRAFFIC_INDEX, PDFIdentity, ReportLink
    link = ReportLink(url=url, series=TRAFFIC, matter_id=None, title="Jan", source_page=TRAFFIC_INDEX, link_text="Jan")
    identity = PDFIdentity(sha256=sha, size_bytes=1, page_count=1, period_start="2025-01-01",
                           period_end="2025-01-31", period_evidence="MONTH ENDED: JANUARY 31, 2025", period_pdf_page=1,
                           processing_status="candidate")
    return link, identity


def test_known_candidate_is_promoted_when_its_bytes_become_admitted():
    from datetime import datetime, timezone
    from mia_capital_intelligence.discovery_catalog import observe
    link, identity = _candidate("d" * 64)
    when = datetime(2026, 11, 22, tzinfo=timezone.utc)
    catalog = {"schema_version": 1, "documents": [], "locations": [], "events": []}
    observe(catalog, link, identity, {"etag": "v1"}, when)
    assert catalog["documents"][0]["dataset_status"] == "not_included"
    # Same URL and bytes, now admitted: the status must change even though the location is unchanged.
    assert observe(catalog, link, identity, {"etag": "v1"}, when, admitted={"d" * 64: "traffic_monthly"}) is True
    doc = catalog["documents"][0]
    assert doc["dataset_status"] == "admitted_elsewhere" and doc["admitted_series"] == "traffic_monthly"
    assert len(catalog["events"]) == 1
    # A later scan with the same inputs changes nothing further.
    assert observe(catalog, link, identity, {"etag": "v1"}, when, admitted={"d" * 64: "traffic_monthly"}) is False


def test_known_candidate_at_a_new_url_is_promoted_when_its_bytes_become_admitted():
    from datetime import datetime, timezone
    from mia_capital_intelligence.discovery_catalog import observe
    link, identity = _candidate("e" * 64)
    other_link, _ = _candidate("e" * 64, url="https://www.miami-airport.com/library/pdfdoc/Airport%20Stats/y.pdf")
    when = datetime(2026, 11, 22, tzinfo=timezone.utc)
    catalog = {"schema_version": 1, "documents": [], "locations": [], "events": []}
    observe(catalog, link, identity, {}, when)
    assert observe(catalog, other_link, identity, {}, when, admitted={"e" * 64: "traffic_monthly"}) is True
    doc = catalog["documents"][0]
    assert doc["dataset_status"] == "admitted_elsewhere" and doc["admitted_series"] == "traffic_monthly"


def test_included_document_is_never_changed_by_the_admission_index():
    from datetime import datetime, timezone
    from mia_capital_intelligence.discovery_catalog import observe
    link, identity = _candidate("f" * 64)
    when = datetime(2026, 11, 22, tzinfo=timezone.utc)
    catalog = {"schema_version": 1, "documents": [], "locations": [], "events": []}
    observe(catalog, link, identity, {}, when)
    catalog["documents"][0]["dataset_status"] = "included"
    catalog["documents"][0]["processing_status"] = "included"
    before = copy.deepcopy(catalog)
    observe(catalog, link, identity, {}, when, admitted={"f" * 64: "traffic_monthly"})
    assert catalog == before


def test_merge_promotes_a_not_included_history_row_to_admitted_elsewhere():
    from mia_capital_intelligence.discovery_catalog import merge_catalogs, validate_catalog
    base = copy.deepcopy(CATALOG)
    previous = copy.deepcopy(base)
    row = copy.deepcopy(next(d for d in base["documents"] if d["dataset_status"] == "admitted_elsewhere"))
    row["dataset_status"], row["processing_status"] = "not_included", "candidate"
    row.pop("admitted_series", None)
    previous["documents"] = [row]
    previous["locations"], previous["events"] = [], []
    validate_catalog(previous)
    merged = merge_catalogs(base, previous)
    merged_row = next(d for d in merged["documents"] if d["sha256"] == row["sha256"])
    assert merged_row["dataset_status"] == "admitted_elsewhere"
    assert merged_row["admitted_series"] == "traffic_monthly"


def test_merge_does_not_demote_or_alter_an_included_history_row():
    from mia_capital_intelligence.discovery_catalog import merge_catalogs
    base = copy.deepcopy(CATALOG)
    included = copy.deepcopy(next(d for d in base["documents"] if d["dataset_status"] == "admitted_elsewhere"))
    included["dataset_status"], included["processing_status"] = "included", "included"
    included.pop("admitted_series", None)
    previous = copy.deepcopy(base)
    previous["documents"] = [included]
    previous["locations"], previous["events"] = [], []
    merged = merge_catalogs(base, previous)
    merged_row = next(d for d in merged["documents"] if d["sha256"] == included["sha256"])
    assert merged_row["dataset_status"] == "included" and "admitted_series" not in merged_row
