"""Public registry integrity, literal search and observation/entity boundaries."""

import json
import shutil
from collections import Counter
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from mia_capital_intelligence import public_registry
from mia_capital_intelligence.directory_queries import (
    DirectoryFilters, UNKNOWN, airport_classification, format_usd, readable_name,
    search_records, source_detail,
)
from mia_capital_intelligence.public_registry import ROOT, build_registry, load_registry, validate_registry


@pytest.fixture(scope="module")
def registry():
    return load_registry()


@pytest.fixture
def payload():
    return json.loads((ROOT / "data/public/registry.json").read_text())


def test_public_coverage_counts_reconcile_without_project_deduplication(registry):
    assert len(registry.records) == 222
    assert len(registry.candidate_links) == 107
    assert registry.verified_projects == ()
    assert [(row["matter_id"], row["indexed_record_count"]) for row in registry.catalog] == [
        ("260526", 110), ("261402", 112), ("261400", 0),
    ]
    assert sum(row["indexed_record_count"] for row in registry.catalog) == len(registry.records)
    assert len({row.source_ref for row in registry.records}) == 222
    assert len(search_records(registry)) == 222


@pytest.mark.parametrize("mutation", [
    "duplicate", "missing", "amount_swap", "wrong_checksum", "wrong_page",
    "invented_identity", "wrong_link", "empty_description", "wrong_inventory",
])
def test_corrupt_registry_is_rejected(payload, mutation):
    records = payload["records"]
    if mutation == "duplicate":
        records.append(deepcopy(records[0]))
    elif mutation == "missing":
        records.pop(0)
    elif mutation == "amount_swap":
        # Swapping the complete cells preserves the page sum and raw/parsed agreement.
        records[0]["metrics"], records[1]["metrics"] = records[1]["metrics"], records[0]["metrics"]
    elif mutation == "wrong_checksum":
        records[0]["document_sha256"] = "0" * 64
    elif mutation == "wrong_page":
        records[0]["pdf_page"] = 8
    elif mutation == "invented_identity":
        payload["verified_projects"] = [{"project_id": "auto-matched"}]
    elif mutation == "wrong_link":
        payload["candidate_links"][0]["identity_status"] = "verified"
    elif mutation == "empty_description":
        records[0]["description_raw"] = ""
    elif mutation == "wrong_inventory":
        payload["source_inventory_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        validate_registry(payload)


@pytest.mark.parametrize(
    ("description", "code"),
    [
        ("MIA E Satellite Terminal Seating Ph2", "MIA"),
        ("TMB New ATCT", "TMB"), ("OPF Engine Run-Up Pad", "OPF"),
        ("MiamiHomestead General Aviation (X51) Security Project", "X51"),
        ("Miami Bldg. 3030 E-Wing Renovation", None), ("Unspecified airport building", None),
        ("MIA and OPF shared scope", None), ("mia Terminal", "MIA"),
    ],
)
def test_airport_classification_uses_documented_tokens_only(description, code):
    assert airport_classification(description)[0] == code


def test_airport_coverage_and_unknowns(registry):
    counts = Counter(airport_classification(row.description_raw)[0] for row in registry.records)
    assert counts == {"MIA": 187, "OPF": 12, "TMB": 6, "X51": 2, None: 15}
    unknown = search_records(registry, DirectoryFilters(airport="Unknown"))
    assert len(unknown) == 15
    assert all(row["airport_code"] is None for row in unknown)


def test_id_search_retains_two_unverified_observations(registry):
    results = search_records(registry, DirectoryFilters(search="ca176a"))
    assert [(row["project_id"], row["matter_id"]) for row in results] == [
        ("CA176A", "261402"), ("CA176A", "260526"),
    ]
    assert all(row["estimate_usd"] == Decimal("3191832.00") for row in results)
    detail = source_detail(registry, results[0]["source_ref"])
    assert detail["verified_project_id"] is None
    assert detail["identity_status"] == "candidate_unverified"
    assert detail["candidate_source_refs"] == [results[1]["source_ref"]]


def test_keyword_facility_airport_and_source_filters(registry):
    rows = search_records(registry, DirectoryFilters(search="Satellite Seating", matter_id="261402", airport="MIA"))
    assert {row["project_id"] for row in rows} == {"CA176A", "CA176B"}
    rows = search_records(registry, DirectoryFilters(search="Miami Executive Airport", airport="TMB"))
    assert len(rows) == 6
    assert all(row["airport_code"] == "TMB" for row in rows)


@pytest.mark.parametrize("search", ["%", "_", "' OR TRUE --", "no-such-public-record"])
def test_search_is_literal_and_empty_results_are_valid(registry, search):
    assert search_records(registry, DirectoryFilters(search=search)) == []


def test_sorting_is_stable_and_financial_values_are_exact(registry):
    filters = DirectoryFilters(sort="Reported estimate, highest first")
    first = search_records(registry, filters)
    assert first == search_records(registry, filters)
    values = [row["estimate_usd"] for row in first]
    assert values == sorted(values, reverse=True)
    assert all(isinstance(value, Decimal) for value in values)
    with pytest.raises(ValueError, match="Unknown directory sort"):
        search_records(registry, DirectoryFilters(sort="SQL injection"))


def test_all_source_urls_and_page_locators_match_catalog(registry):
    for row in registry.records:
        detail = source_detail(registry, row.source_ref)
        assert detail["source_page_url"] == f"{detail['source']['url']}#page={row.pdf_page}"
        assert detail["source"]["sha256"] == row.document_sha256
        assert detail["pdf_page_index"] == row.pdf_page - 1
        assert detail["printed_page"] == f"MDC{row.pdf_page:03}"
        assert detail["estimate_raw"] == row.metrics["total_estimated_cost_usd"].raw_value
        assert detail["verified_project_id"] is None
        assert detail["reported_status"] is detail["milestone"] is detail["facility"] is None


def test_detail_keeps_one_sided_records_without_lifecycle_claims(registry):
    row = next(row for row in registry.records if row.project_id == "T180D")
    detail = source_detail(registry, row.source_ref)
    assert detail["identity_status"] == "document_scoped_record"
    assert detail["candidate_source_refs"] == []
    assert "delta" not in detail and "cost_growth" not in detail
    with pytest.raises(ValueError, match="not in this published registry"):
        source_detail(registry, "unknown-source-record")


def test_unknown_values_and_display_normalization():
    assert format_usd(None) == UNKNOWN
    assert format_usd(Decimal("0")) == "$ 0"
    assert format_usd(Decimal("3191832")) == "$ 3,191,832"
    assert format_usd(Decimal("1.01")) == "$ 1.01"
    assert readable_name("MIA\nGates&nbsp; F4") == "MIA Gates F4"


def test_public_runtime_does_not_require_raw_pdfs_or_review_approvals(tmp_path):
    for relative in ("data/source_inventory.json", "data/audit/exhibit_b_row_controls.csv", "data/public/registry.json"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    assert not (tmp_path / "data/raw").exists()
    assert not (tmp_path / "data/review_dispositions.json").exists()
    registry = load_registry(tmp_path)
    assert len(search_records(registry, DirectoryFilters(search="CA176A"))) == 2


@pytest.mark.integration
def test_rebuild_is_reproducible_and_failure_preserves_previous_artifact(tmp_path, monkeypatch):
    if any(not (ROOT / f"data/raw/{matter}.pdf").is_file() for matter in ("260526", "261402", "261400")):
        pytest.skip("Pinned originals required to rebuild public inputs")
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    build_registry(output=first)
    build_registry(output=second)
    assert first.read_bytes() == second.read_bytes() == (ROOT / "data/public/registry.json").read_bytes()
    previous = first.read_bytes()

    def fail_extraction(root):
        raise ValueError("Synthetic failed extraction")

    monkeypatch.setattr(public_registry, "load_exhibit_b", fail_extraction)
    with pytest.raises(ValueError, match="Synthetic failed extraction"):
        build_registry(output=first)
    assert first.read_bytes() == previous
