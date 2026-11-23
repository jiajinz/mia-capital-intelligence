"""Golden digests and control totals for the tracked, PDF-free artifacts.

These checks run in CI without the pinned PDFs. A tracked artifact that changes must
update its pin here in the same reviewed change. Digests were computed from the bytes of
origin/main (git show origin/main:<path> | shasum -a 256) when this test was added.
"""

import csv
import json
from hashlib import sha256
from pathlib import Path

import pytest

from mia_capital_intelligence.contract_spending import INPUT_PATH, read_financial_input
from mia_capital_intelligence.discovery_catalog import admitted_elsewhere_index
from mia_capital_intelligence.public_registry import load_registry
from mia_capital_intelligence.row_controls import load_page_controls

ROOT = Path(__file__).resolve().parents[1]

# SHA-256 of each tracked artifact, from origin/main.
ARTIFACT_SHA256 = {
    "data/public/registry.json": "4d8b44bb6791777e3107395609f607dfcd5908fa24954864c039df79d665a438",
    "data/financial/snapshots.v1.json": "3c90df7ea841061823781be3aa6a388f18c82d51fcf317c3d7f7b261a11622be",
    "data/audit/exhibit_b_row_controls.csv": "4c83db3fb8de3d7faff428ed45e27f7ca1eb938f29da1185e0d1cbfb10e58627",
    "data/source_inventory.json": "ac4659ffb63c7be3b02e8809ea7041e93113aedc89d5c62d5c8879dd51f92437",
    "data/traffic/traffic_capacity.v1.json": "61300ccd834befa201796397d636d3acad3e9b0b3e7970e8f51f6b7d2be3ce30",
    "data/traffic/traffic_monthly.expansion_2018_2023.v1.json": "cd25590807f196f407e7b152df4dc6e8f42205e8649fa708b3cd1ce38be62de2",
    "data/traffic/traffic_monthly.gap_2015_2017.v1.json": "4e96aa95fb0adfac14228e305c679c0aa40d5402f60d50c741357f77eb5c9d51",
    "data/traffic/traffic_monthly.html_2010_2017.v1.json": "840ac459c86df41d5485caede698bde1e04e0e3a1dc7a8bb10c6363885b3c6c7",
    "data/traffic/traffic_monthly.plan_a.v1.json": "3aa5ee913ac49ca6df73904fc2a7224188ba74682c96d79bbcf6df1f8fd1cbe6",
    "data/traffic/traffic_monthly.resolved_2012_2014.v1.json": "ec4f7a94f6af5f4b687634e4b814901e1ff1de53d712c786e620040cd4fdbbb5",
}

# Control totals derived from the tracked files above.
# Registry records: len(records) in data/public/registry.json (222, matching the indexed
# Exhibit B rows asserted by tests/test_public_registry.py).
REGISTRY_RECORD_COUNT = 332
# Row controls: data rows, excluding the header, in data/audit/exhibit_b_row_controls.csv.
ROW_CONTROL_COUNT = 332
# Admitted traffic months: distinct periods across the admitted rows of
# data/traffic/traffic_monthly.*.json. The union equals the 199 distinct periods of
# data/traffic/traffic_capacity.v1.json (its scope text says 199 admitted months).
ADMITTED_TRAFFIC_MONTHS = 199

ROW_CONTROL_HEADER = [
    "matter_id", "source_sha256", "exhibit", "pdf_page", "printed_page", "row_ordinal", "project_id", "amount_usd",
]
REGISTRY_KEYS = {
    "schema_version", "source_inventory_sha256", "source_versions", "records",
    "verified_projects", "project_memberships", "candidate_links",
}
TRAFFIC_KEYS = {"schema_version", "dataset_version", "status", "admitted_by", "admitted_at", "rows"}


def _bytes(relative: str) -> bytes:
    return (ROOT / relative).read_bytes()


def _json(relative: str) -> dict:
    return json.loads(_bytes(relative).decode("utf-8"))


def _traffic_monthly_files() -> list[str]:
    return sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "data/traffic").glob("traffic_monthly.*.json"))


def _admitted_traffic_periods() -> set[str]:
    periods: set[str] = set()
    for relative in _traffic_monthly_files():
        periods.update(row["period"] for row in _json(relative)["rows"] if row.get("status") == "admitted")
    return periods


def _csv_rows() -> tuple[list[str], list[dict[str, str]]]:
    with (ROOT / "data/audit/exhibit_b_row_controls.csv").open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


@pytest.mark.parametrize("relative", sorted(ARTIFACT_SHA256))
def test_tracked_artifact_sha256_matches_pin(relative):
    expected = ARTIFACT_SHA256[relative]
    actual = sha256(_bytes(relative)).hexdigest()
    assert actual == expected, f"{relative}: sha256 expected {expected}, found {actual}"


def test_pinned_digests_cover_every_traffic_json_file():
    found = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "data/traffic").glob("*.json"))
    pinned = sorted(path for path in ARTIFACT_SHA256 if path.startswith("data/traffic/"))
    assert found == pinned, f"data/traffic/*.json: expected pinned files {pinned}, found {found}"


def test_registry_loads_through_public_loader_with_pinned_record_count():
    registry = load_registry()
    actual = len(registry.records)
    assert actual == REGISTRY_RECORD_COUNT, (
        f"data/public/registry.json record count: expected {REGISTRY_RECORD_COUNT}, found {actual}"
    )


def test_registry_has_expected_top_level_keys():
    keys = set(_json("data/public/registry.json"))
    assert keys == REGISTRY_KEYS, (
        f"data/public/registry.json top-level keys: expected {sorted(REGISTRY_KEYS)}, found {sorted(keys)}"
    )


def test_row_control_header_and_count_match_pins():
    header, rows = _csv_rows()
    assert header == ROW_CONTROL_HEADER, (
        f"data/audit/exhibit_b_row_controls.csv header: expected {ROW_CONTROL_HEADER}, found {header}"
    )
    assert len(rows) == ROW_CONTROL_COUNT, (
        f"data/audit/exhibit_b_row_controls.csv row count: expected {ROW_CONTROL_COUNT}, found {len(rows)}"
    )


def test_row_controls_load_through_page_loader_with_inventory_digests():
    inventory = {source["matter_id"]: source["sha256"] for source in _json("data/source_inventory.json")["sources"]}
    _, rows = _csv_rows()
    path = ROOT / "data/audit/exhibit_b_row_controls.csv"
    pages = sorted({(row["matter_id"], int(row["pdf_page"])) for row in rows})
    loaded = 0
    for matter, page in pages:
        loaded += len(load_page_controls(path, matter_id=matter, source_sha256=inventory[matter], pdf_page=page))
    assert loaded == ROW_CONTROL_COUNT, (
        f"data/audit/exhibit_b_row_controls.csv page-loaded rows: expected {ROW_CONTROL_COUNT}, found {loaded}"
    )


def test_financial_snapshot_loads_through_pinned_reader():
    expected = ARTIFACT_SHA256["data/financial/snapshots.v1.json"]
    result = read_financial_input(ROOT / INPUT_PATH)
    assert result.digest == expected, (
        f"data/financial/snapshots.v1.json: sha256 expected {expected}, found {result.digest}"
    )


def test_source_inventory_has_four_sources_and_expected_keys():
    payload = _json("data/source_inventory.json")
    assert "sources" in payload, "data/source_inventory.json: missing 'sources' key"
    matters = sorted(source["matter_id"] for source in payload["sources"])
    assert matters == ["260526", "261400", "261402", "261824"], (
        f"data/source_inventory.json matter_ids: expected four sources, found {matters}"
    )


def test_traffic_files_have_expected_header_and_are_admitted():
    for relative in sorted(ARTIFACT_SHA256):
        if not relative.startswith("data/traffic/"):
            continue
        payload = _json(relative)
        missing = TRAFFIC_KEYS - set(payload)
        assert not missing, f"{relative}: missing header keys {sorted(missing)}"
        assert payload["status"] == "admitted", f"{relative}: status expected 'admitted', found {payload['status']!r}"


def test_admitted_elsewhere_index_reads_all_traffic_files():
    index = admitted_elsewhere_index(ROOT)
    assert index, "data/traffic/*.json: admitted_elsewhere_index returned no source digests"
    series = set(index.values())
    assert series == {"traffic_monthly"}, (
        f"data/traffic/*.json admitted series: expected {{'traffic_monthly'}}, found {sorted(series)}"
    )


def test_admitted_traffic_month_count_matches_pin_and_capacity_scope():
    periods = _admitted_traffic_periods()
    assert len(periods) == ADMITTED_TRAFFIC_MONTHS, (
        f"admitted traffic months in {_traffic_monthly_files()}: "
        f"expected {ADMITTED_TRAFFIC_MONTHS}, found {len(periods)}"
    )
    capacity = {row["period"] for row in _json("data/traffic/traffic_capacity.v1.json")["rows"]}
    assert periods == capacity, (
        f"admitted traffic months differ from data/traffic/traffic_capacity.v1.json: "
        f"only in monthly series {sorted(periods - capacity)}, only in capacity {sorted(capacity - periods)}"
    )
