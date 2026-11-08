"""Rebuild and validate the public source-record registry independently of approvals."""

import argparse
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import duckdb

from mia_capital_intelligence.comparability_model import AmountObservation, SourceRecord, candidate_id
from mia_capital_intelligence.row_controls import ProfileRow, load_page_controls, validate_page_rows
from mia_capital_intelligence.source_identity import verify_pdf
from mia_capital_intelligence.source_records import load_exhibit_b

ROOT = Path(__file__).resolve().parents[2]
INDEXED_PAGES = {"260526": (11, 12), "261402": (12, 13)}
METRIC = "total_estimated_cost_usd"
AIRPORTS = {
    "MIA": "Miami International Airport",
    "OPF": "Miami-Opa locka Executive Airport",
    "TMB": "Miami Executive Airport",
    "X51": "Miami Homestead General Aviation Airport",
}


@dataclass(frozen=True)
class PublicRegistry:
    """Document-scoped observations, candidate links and a separate identity relation."""

    catalog: tuple[dict[str, Any], ...]
    records: tuple[SourceRecord, ...]
    candidate_links: tuple[dict[str, str], ...]
    verified_projects: tuple[dict[str, Any], ...] = ()


def registry_candidate_links(records: tuple[SourceRecord, ...]) -> list[dict[str, str]]:
    """Reuse the exact-ID SQL matcher without requiring analytical comparison approval."""
    with duckdb.connect(":memory:") as connection:
        connection.execute(
            "CREATE TABLE source_rows (source_ref VARCHAR, matter_id VARCHAR, exhibit VARCHAR, project_id VARCHAR)"
        )
        if records:
            connection.executemany("INSERT INTO source_rows VALUES (?, ?, ?, ?)", [
                (row.source_ref, row.matter_id, row.exhibit, row.project_id) for row in records
            ])
        matches = connection.execute(
            (Path(__file__).with_name("sql") / "candidates.sql").read_text(),
            list(INDEXED_PAGES),
        ).fetchall()
    return [
        {"candidate_id": candidate_id(earlier, later), "project_id": project_id,
         "earlier_ref": earlier, "later_ref": later, "identity_status": "candidate_unverified"}
        for project_id, earlier, later in matches if earlier is not None and later is not None
    ]


def _record_from_json(raw: dict[str, Any]) -> SourceRecord:
    if set(raw) != {
        "source_ref", "matter_id", "document_sha256", "exhibit", "pdf_page", "row_ordinal",
        "project_id", "description_raw", "metrics", "bbox",
    } or set(raw["metrics"]) != {METRIC}:
        raise ValueError("Unexpected public source-record schema")
    cell = raw["metrics"][METRIC]
    value = Decimal(cell["value"])
    parsed_raw = Decimal(int("".join(cell["raw_value"].split()).removeprefix("$").replace(",", "")))
    if not value.is_finite() or value != parsed_raw or cell["unit"] != "USD":
        raise ValueError(f"{raw['source_ref']}: estimate differs from original cell")
    record = SourceRecord(
        raw["matter_id"], raw["document_sha256"], raw["exhibit"], raw["pdf_page"],
        raw["row_ordinal"], raw["project_id"], raw["description_raw"],
        {METRIC: AmountObservation(
            value, cell["raw_value"], cell["original_header"], cell["unit"],
            cell["verification_status"],
        )}, tuple(raw["bbox"]) if raw["bbox"] is not None else None,
    )
    if raw["source_ref"] != record.source_ref or not record.description_raw.strip():
        raise ValueError(f"{raw['source_ref']}: invalid row reference or missing description")
    if cell["verification_status"] != "machine_cross_checked" or "Total Estimated" not in cell["original_header"]:
        raise ValueError(f"{raw['source_ref']}: invalid metric evidence")
    return record


def validate_registry(payload: dict[str, Any], root: Path = ROOT) -> PublicRegistry:
    """Fail on missing/duplicate rows, stale provenance or invented verified identities."""
    inventory_path = root / "data/source_inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))["sources"]
    if payload["schema_version"] != "1.0" or payload["source_inventory_sha256"] != sha256(inventory_path.read_bytes()).hexdigest():
        raise ValueError("Registry schema or source inventory identity differs")
    if payload["verified_projects"] or payload["project_memberships"]:
        raise ValueError("Stage 1 has no reviewed cross-document project identities")
    sources = {source["matter_id"]: source for source in inventory}
    if payload["source_versions"] != {key: source["sha256"] for key, source in sources.items()}:
        raise ValueError("Registry source versions differ from the catalog")
    records = tuple(_record_from_json(row) for row in payload["records"])
    if len({row.source_ref for row in records}) != len(records):
        raise ValueError("Duplicate public source-record reference")
    for row in records:
        if (
            row.matter_id not in INDEXED_PAGES or row.exhibit != "B"
            or row.pdf_page not in INDEXED_PAGES[row.matter_id]
            or row.document_sha256 != sources[row.matter_id]["sha256"]
        ):
            raise ValueError(f"{row.source_ref}: source version or exhibit differs")
    for matter, pages in INDEXED_PAGES.items():
        for page in pages:
            selected = sorted(
                (row for row in records if row.matter_id == matter and row.pdf_page == page),
                key=lambda row: row.row_ordinal,
            )
            if [row.row_ordinal for row in selected] != list(range(1, len(selected) + 1)):
                raise ValueError(f"{matter} p.{page}: source-row ordinals differ")
            validate_page_rows(
                [ProfileRow(row.project_id, int(row.metrics[METRIC].value)) for row in selected],
                load_page_controls(root / "data/audit/exhibit_b_row_controls.csv", matter_id=matter,
                                   source_sha256=sources[matter]["sha256"], pdf_page=page),
                context=f"Public registry {matter} B p.{page}",
            )
    links = registry_candidate_links(records)
    if payload["candidate_links"] != links:
        raise ValueError("Candidate identity links differ from the controlled source records")
    catalog = []
    for source in inventory:
        parsed = urlparse(source["url"])
        if parsed.scheme != "https" or parsed.hostname != "www.miamidade.gov":
            raise ValueError(f"{source['matter_id']}: unexpected official document URL")
        count = sum(row.matter_id == source["matter_id"] for row in records)
        catalog.append({
            **source, "publishing_organization": "Miami-Dade Aviation Department / Miami-Dade County",
            "indexed_record_count": count,
            "indexed_pdf_pages": list(INDEXED_PAGES.get(source["matter_id"], ())),
            "indexing_status": "Exhibit B partially indexed" if count else "Cataloged only",
            "validation_status": "IDs and estimates cross-checked" if count else "Document identity verified at build",
            "coverage_limit": (
                "Only Exhibit B project IDs, descriptions and total estimated costs are indexed. "
                "Other exhibits, narrative, progress and milestones remain outside the public index."
                if count else "No project records from this report are indexed in the public directory."
            ),
        })
    return PublicRegistry(tuple(catalog), records, tuple(links))


def _decimal_json(value: Any) -> str:
    if isinstance(value, Decimal):
        return format(value, ".2f")
    raise TypeError(f"Unexpected registry value: {type(value).__name__}")


def build_registry(root: Path = ROOT, output: Path | None = None) -> PublicRegistry:
    """Validate all source bytes, build in memory and atomically replace one JSON artifact."""
    inventory_path = root / "data/source_inventory.json"
    sources = json.loads(inventory_path.read_text(encoding="utf-8"))["sources"]
    for source in sources:
        verify_pdf(root / f"data/raw/{source['matter_id']}.pdf",
                   expected_size=source["size_bytes"], expected_sha256=source["sha256"])
    _, extracted = load_exhibit_b(root)
    records = tuple(extracted)
    payload = {
        "schema_version": "1.0",
        "source_inventory_sha256": sha256(inventory_path.read_bytes()).hexdigest(),
        "source_versions": {source["matter_id"]: source["sha256"] for source in sources},
        "records": [{"source_ref": row.source_ref, **asdict(row)} for row in records],
        "verified_projects": [], "project_memberships": [],
        "candidate_links": registry_candidate_links(records),
    }
    encoded = json.dumps(payload, default=_decimal_json, indent=2, sort_keys=True) + "\n"
    registry = validate_registry(json.loads(encoded), root)
    target = output or root / "data/public/registry.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return registry


def load_registry(root: Path = ROOT) -> PublicRegistry:
    """Read a prebuilt artifact. Runtime operation requires no PDF or file writes."""
    payload = json.loads((root / "data/public/registry.json").read_text(encoding="utf-8"))
    return validate_registry(payload, root)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the public MIA source-record registry")
    parser.add_argument("command", choices=["build", "check"])
    args = parser.parse_args()
    registry = build_registry() if args.command == "build" else load_registry()
    print(json.dumps({
        "source_records": len(registry.records), "cataloged_documents": len(registry.catalog),
        "indexed_documents": sum(row["indexed_record_count"] > 0 for row in registry.catalog),
        "candidate_links": len(registry.candidate_links),
        "verified_cross_document_projects": len(registry.verified_projects),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
