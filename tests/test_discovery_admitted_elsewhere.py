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
