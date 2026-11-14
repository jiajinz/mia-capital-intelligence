"""Public search and evidence queries over individually validated observations."""

import html
import re
from bisect import bisect_right
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb

from mia_capital_intelligence.project_delivery import DELIVERY_BY_SOURCE_REF
from mia_capital_intelligence.public_registry import AIRPORTS, METRIC, PublicRegistry

UNKNOWN = "Not reported in the indexed fields"
ESTIMATE_BANDS = ("Under $10M", "$10M to under $50M", "$50M to under $100M", "$100M or more")
ESTIMATE_THRESHOLDS = (10_000_000, 50_000_000, 100_000_000)
PROJECT_BRIEFS = {
    ("V008B", "MIA New Concourse F MIA Concourse F Modernization (Gates F4,F6, F8 Gates Building Expansion)"):
        "Modernize Concourse F at Miami International Airport and expand building space at gates F4, F6 and F8.",
    ("T180B", "MIA Cc D - West Extension D60 Ph 2 (Bldg. Expansion & Apron)"):
        "Extend Concourse D west at Gate D60. Phase 2 covers building expansion and the apron area.",
    ("U010D-I", "MIA Satellite E New Chiller Plant"):
        "Build a new cooling plant for Satellite E at Miami International Airport.",
}
SORTS = {
    "Project ID": "project_id ASC, period_start DESC, source_ref ASC",
    "Project name": "project_name ASC, period_start DESC, source_ref ASC",
    "Reported estimate, highest first": "estimate_usd DESC NULLS LAST, project_id ASC, source_ref ASC",
    "Report period, newest first": "period_start DESC, project_id ASC, source_ref ASC",
}


@dataclass(frozen=True)
class DirectoryFilters:
    """Literal keywords and source-backed facets for source-record search."""

    search: str = ""
    airport: str | None = None
    matter_id: str | None = None
    sort: str = "Project ID"


def airport_classification(description: str) -> tuple[str | None, str]:
    """Use explicit source tokens only and preserve missing or ambiguous locations."""
    codes = set(re.findall(r"\b(?:MIA|OPF|TMB|X51)\b", description, flags=re.IGNORECASE))
    codes = {code.upper() for code in codes}
    if len(codes) == 1:
        code = next(iter(codes))
        return code, f"Explicit {code} token in the original project description"
    if codes:
        return None, "Multiple airport codes in the source description; location unresolved"
    return None, "No indexed airport code in the source description"


def readable_name(description: str) -> str:
    """Normalize whitespace and literal HTML entities for readable display."""
    return " ".join(html.unescape(description).split())


def format_usd(value: Decimal | None) -> str:
    """Display an exact source estimate with its reported whole-dollar precision."""
    if value is None:
        return UNKNOWN
    if value == value.to_integral_value():
        return f"$ {value:,.0f}"
    return f"$ {value:,.2f}"


def estimate_band(value: Decimal | None) -> str | None:
    """Group a known estimate using inclusive lower bounds."""
    return None if value is None else ESTIMATE_BANDS[bisect_right(ESTIMATE_THRESHOLDS, value)]


def search_records(registry: PublicRegistry, filters: DirectoryFilters = DirectoryFilters()) -> list[dict[str, Any]]:
    """Return source observations with parameterized DuckDB search and stable sorting."""
    if filters.sort not in SORTS:
        raise ValueError(f"Unknown directory sort: {filters.sort}")
    sources = {source["matter_id"]: source for source in registry.catalog}
    rows = []
    for record in registry.records:
        airport, _ = airport_classification(record.description_raw)
        source = sources[record.matter_id]
        rows.append((
            record.source_ref, record.project_id, readable_name(record.description_raw),
            record.description_raw, airport, AIRPORTS.get(airport, "Unknown airport"),
            record.matter_id, source["period_start"], source["period_end"],
            record.metrics[METRIC].value, record.pdf_page,
        ))
    conditions = []
    parameters: list[Any] = []
    for keyword in filters.search.split():
        conditions.append("contains(lower(project_id || ' ' || project_name || ' ' || airport_name), lower(?))")
        parameters.append(keyword)
    if filters.airport is not None:
        conditions.append("airport_code IS NULL" if filters.airport == "Unknown" else "airport_code = ?")
        if filters.airport != "Unknown":
            parameters.append(filters.airport)
    if filters.matter_id is not None:
        conditions.append("matter_id = ?")
        parameters.append(filters.matter_id)
    where = " AND ".join(conditions) if conditions else "TRUE"
    with duckdb.connect(":memory:") as connection:
        connection.execute("""
            CREATE TABLE directory_records (
                source_ref VARCHAR PRIMARY KEY, project_id VARCHAR, project_name VARCHAR,
                description_raw VARCHAR, airport_code VARCHAR, airport_name VARCHAR,
                matter_id VARCHAR, period_start VARCHAR, period_end VARCHAR,
                estimate_usd DECIMAL(18,2), pdf_page INTEGER
            )
        """)
        if rows:
            connection.executemany("INSERT INTO directory_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
        query = (Path(__file__).with_name("sql") / "directory.sql").read_text()
        result = connection.execute(query.format(where=where, order_by=SORTS[filters.sort]), parameters)
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]


def source_detail(registry: PublicRegistry, source_ref: str) -> dict[str, Any]:
    """Return one source record and explicitly unverified candidate references."""
    record = next((row for row in registry.records if row.source_ref == source_ref), None)
    if record is None:
        raise ValueError("The selected source record is not in this published registry")
    source = next(row for row in registry.catalog if row["matter_id"] == record.matter_id)
    airport, reason = airport_classification(record.description_raw)
    name = readable_name(record.description_raw)
    related = [
        link["later_ref"] if link["earlier_ref"] == source_ref else link["earlier_ref"]
        for link in registry.candidate_links
        if source_ref in {link["earlier_ref"], link["later_ref"]}
    ]
    return {
        "source_ref": source_ref, "project_id": record.project_id,
        "project_name": name, "description_raw": record.description_raw,
        "project_brief": PROJECT_BRIEFS.get((record.project_id, name), name),
        "reporting_agency": source["publishing_organization"],
        "delivery": DELIVERY_BY_SOURCE_REF.get(source_ref),
        "airport_code": airport, "airport_name": AIRPORTS.get(airport, "Unknown airport"),
        "airport_evidence": reason, "category": "Capital Improvement Program",
        "facility": None, "reported_status": None, "milestone": None,
        "estimate_usd": record.metrics[METRIC].value, "estimate_raw": record.metrics[METRIC].raw_value,
        "estimate_header": record.metrics[METRIC].original_header,
        "metric": METRIC, "source": source,
        "pdf_page": record.pdf_page, "pdf_page_index": record.pdf_page - 1,
        "printed_page": f"MDC{record.pdf_page:03}", "row_ordinal": record.row_ordinal,
        "bbox": record.bbox, "source_page_url": f"{source['url']}#page={record.pdf_page}",
        "verified_project_id": None,
        "identity_status": "candidate_unverified" if related else "document_scoped_record",
        "candidate_source_refs": related,
        "validation_status": "Project ID and estimate matched independent row controls",
        "description_status": "Original source-row text retained; display spacing normalized",
    }
