"""Versioned candidate metadata; this catalog is separate from application inputs."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import asdict
from datetime import date, datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from mia_capital_intelligence.discovery_sources import MONTHLY, QUARTERLY, PDFIdentity, ReportLink, official_url

CATALOG_PATH = Path("data/discovery/catalog.json")
LOG_PATH = Path("docs/DATA_UPDATES.md")
BEGIN = "<!-- BEGIN DISCOVERY EVENTS -->"
END = "<!-- END DISCOVERY EVENTS -->"


def read_catalog(path: Path) -> dict[str, Any]:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    validate_catalog(catalog)
    return catalog


def validate_catalog(catalog: dict[str, Any]) -> None:
    """Check referential integrity as well as the machine-readable JSON schema."""
    from jsonschema import Draft202012Validator

    schema = Path(__file__).resolve().parents[2] / "schemas/discovery_catalog.schema.json"
    Draft202012Validator(json.loads(schema.read_text()), format_checker=Draft202012Validator.FORMAT_CHECKER).validate(catalog)
    versions = {row["sha256"]: row for row in catalog["documents"]}
    if len(versions) != len(catalog["documents"]):
        raise ValueError("Duplicate PDF version")
    for document in versions.values():
        source_urls = set()
        for source in document["sources"]:
            if official_url(source["url"]) != source["url"] or source["url"] in source_urls:
                raise ValueError("Invalid or duplicate PDF source")
            source_urls.add(source["url"])
            official_url(source["source_page"])
            if "resolved_url" in source:
                official_url(source["resolved_url"])
        for field in ("period_start", "period_end"):
            if document[field] is not None:
                date.fromisoformat(document[field])
        if (document["period_start"] is None) != (document["period_end"] is None):
            raise ValueError("Incomplete report period")
        if document["period_start"] and document["period_start"] > document["period_end"]:
            raise ValueError("Reversed report period")
    urls = set()
    for location in catalog["locations"]:
        url = official_url(location["url"])
        if url != location["url"] or url in urls or location["sha256"] not in versions:
            raise ValueError("Invalid or duplicate document location")
        urls.add(url)
        official_url(location["source_page"])
        if location["url"] not in {source["url"] for source in versions[location["sha256"]]["sources"]}:
            raise ValueError("Location is missing its version provenance")
    event_ids = set()
    for event in catalog["events"]:
        if event["id"] in event_ids or event["sha256"] not in versions:
            raise ValueError("Invalid or duplicate discovery event")
        if event["previous_sha256"] and event["previous_sha256"] not in versions:
            raise ValueError("Revision has no retained prior version")
        if event["url"] not in {source["url"] for source in versions[event["sha256"]]["sources"]}:
            raise ValueError("Event is missing its PDF source")
        event_ids.add(event["id"])
        official_url(event["url"])
        when = datetime.fromisoformat(event["occurred_at"])
        if when.utcoffset() is None:
            raise ValueError("Discovery events require a timezone")
        if event["pull_request_url"] is not None and not re.fullmatch(
            r"https://github\.com/[^/]+/[^/]+/pull/\d+", event["pull_request_url"]
        ):
            raise ValueError("Invalid discovery pull request URL")


def seed_catalog(root: Path) -> dict[str, Any]:
    """Start from both published inventories; do not invent historical dates."""
    inventory = json.loads((root / "data/source_inventory.json").read_text())["sources"]
    financial = json.loads((root / "data/financial/snapshots.v1.json").read_text())["sources"]
    published = {row["sha256"]: row for row in inventory if row["series"] == QUARTERLY}
    published.update({row["sha256"]: row for row in financial})
    documents, locations = [], []
    for digest, source in published.items():
        is_monthly = "report_month_label" in source
        month = source.get("report_month_label")
        if is_monthly:
            from calendar import monthrange

            year, number = map(int, month.split("-"))
            start, end = date(year, number, 1).isoformat(), date(year, number, monthrange(year, number)[1]).isoformat()
        else:
            start, end = source["period_start"], source["period_end"]
        url = official_url(source["url"])
        title = source.get("title", f"Aviation Capital Program Report — {month}")
        provenance = {"url": url, "source_page": source.get("matter_url", url), "link_text": title}
        documents.append({"sha256": digest, "series": MONTHLY if is_monthly else QUARTERLY,
                          "title": title, "matter_id": source["matter_id"], "size_bytes": source["size_bytes"],
                          "page_count": source["page_count"], "period_start": start, "period_end": end,
                          "period_evidence": "Existing published source metadata", "period_pdf_page": None,
                          "processing_status": "included", "dataset_status": "included",
                          "first_seen_at": None, "sources": [provenance]})
        locations.append({**provenance, "sha256": digest, "etag": None, "last_modified": None})
    catalog = {"schema_version": 1, "documents": sorted(documents, key=lambda row: row["sha256"]),
               "locations": sorted(locations, key=lambda row: row["url"]), "events": []}
    validate_catalog(catalog)
    return catalog


def admitted_elsewhere_index(root: Path) -> dict[str, str]:
    """Map SHA-256 to series for source bytes already admitted in data/traffic (read-only)."""
    index: dict[str, str] = {}
    for path in sorted((root / "data" / "traffic").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        # Only some traffic files carry series_id; the others belong to the same monthly series.
        series = payload.get("series_id", "traffic_monthly")
        for row in payload.get("rows", []):
            digest = row.get("source_sha256")
            if digest:
                index[digest] = series
    return index


def observe(catalog: dict[str, Any], link: ReportLink, identity: PDFIdentity,
            headers: dict[str, str], when: datetime, *, resolved_url: str | None = None,
            admitted: dict[str, str] | None = None) -> bool:
    """Add immutable file versions and retain previous same-URL bytes by hash."""
    if when.utcoffset() is None:
        raise ValueError("Discovery timestamp requires a timezone")
    timestamp = when.astimezone(timezone.utc).isoformat(timespec="seconds")
    url = official_url(link.url)
    location = next((row for row in catalog["locations"] if row["url"] == url), None)
    if location and location["sha256"] == identity.sha256:
        return False
    existing = next((row for row in catalog["documents"] if row["sha256"] == identity.sha256), None)
    if existing and existing["series"] != link.series:
        raise ValueError("Identical PDF bytes classified into conflicting report series")
    if existing and identity.period_start and existing["period_start"] and (
        existing["period_start"], existing["period_end"]
    ) != (identity.period_start, identity.period_end):
        raise ValueError("Identical PDF bytes assigned conflicting reporting periods")
    previous = location["sha256"] if location else None
    kind = "revised" if previous else "source_linked" if existing else "discovered"
    provenance = {"url": url, "source_page": official_url(link.source_page), "link_text": link.link_text[:300]}
    if resolved_url:
        provenance["resolved_url"] = official_url(resolved_url)
    if existing is None:
        admitted_series = (admitted or {}).get(identity.sha256)
        document = {**asdict(identity), "series": link.series, "title": link.title[:300],
                    "matter_id": link.matter_id,
                    "dataset_status": "admitted_elsewhere" if admitted_series else "not_included",
                    "first_seen_at": timestamp, "sources": [provenance]}
        if admitted_series:
            document["admitted_series"] = admitted_series
        catalog["documents"].append(document)
    elif url not in {source["url"] for source in existing["sources"]}:
        existing["sources"].append(provenance)
    new_location = {**provenance, "sha256": identity.sha256,
                    "etag": headers.get("etag"), "last_modified": headers.get("last-modified")}
    if location:
        catalog["locations"].remove(location)
    catalog["locations"].append(new_location)
    event_id = sha256(f"{kind}:{url}:{previous}:{identity.sha256}:{timestamp}".encode()).hexdigest()
    if event_id not in {event["id"] for event in catalog["events"]}:
        catalog["events"].append({"id": event_id, "kind": kind, "occurred_at": timestamp,
                                  "sha256": identity.sha256, "previous_sha256": previous,
                                  "url": url, "pull_request_url": None})
    catalog["documents"].sort(key=lambda row: row["sha256"])
    catalog["locations"].sort(key=lambda row: row["url"])
    return True


def merge_catalogs(base: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    """Carry open or closed candidate history forward without losing published metadata."""
    validate_catalog(base)
    validate_catalog(previous)
    merged = copy.deepcopy(previous)
    versions = {row["sha256"]: row for row in merged["documents"]}
    for published in base["documents"]:
        if published["sha256"] not in versions:
            merged["documents"].append(copy.deepcopy(published))
        elif published["dataset_status"] == "included":
            versions[published["sha256"]]["dataset_status"] = "included"
            versions[published["sha256"]]["processing_status"] = "included"
    locations = {row["url"] for row in merged["locations"]}
    merged["locations"].extend(copy.deepcopy(row) for row in base["locations"] if row["url"] not in locations)
    ids = {row["id"] for row in merged["events"]}
    merged["events"].extend(copy.deepcopy(row) for row in base["events"] if row["id"] not in ids)
    merged["documents"].sort(key=lambda row: row["sha256"])
    merged["locations"].sort(key=lambda row: row["url"])
    validate_catalog(merged)
    return merged


def serialize_catalog(catalog: dict[str, Any]) -> str:
    validate_catalog(catalog)
    return json.dumps(catalog, indent=2, ensure_ascii=True) + "\n"


def label(text: str) -> str:
    return re.sub(r"[<>\[\]`*_\\]", "", " ".join(text.split()))[:300]


def render_log(baseline: str, catalog: dict[str, Any]) -> str:
    """Render candidate events separately from the existing published inventory."""
    if BEGIN in baseline:
        prefix, tail = baseline.split(BEGIN, 1)
        if END not in tail:
            raise ValueError("Incomplete generated data-log section")
        suffix = tail.split(END, 1)[1]
    else:
        prefix, suffix = baseline.rstrip() + "\n\n", "\n"
    lines = [BEGIN, "## Report discovery history", "",
             "These events track official files found by the source monitor. A discovered or revised file is not added to the application dataset by this log.", ""]
    versions = {row["sha256"]: row for row in catalog["documents"]}
    for event in sorted(catalog["events"], key=lambda row: (row["occurred_at"], row["id"]), reverse=True):
        document = versions[event["sha256"]]
        name = {"discovered": "Discovered", "revised": "Revised official file", "source_linked": "Additional source link"}[event["kind"]]
        period = (f"{document['period_start']} to {document['period_end']}" if document["period_start"] else "Unknown")
        lines.extend([f"### {event['occurred_at']} — {name}", "",
                      f"**{label(document['title'])}**" + (f" · Matter {document['matter_id']}" if document["matter_id"] else ""), "",
                      f"- Reporting period: {period}.",
                      f"- [Official PDF](<{event['url']}>) · {document['page_count']} PDF pages.",
                      f"- SHA-256: `{document['sha256']}`."])
        if event["previous_sha256"]:
            lines.append(f"- Previous version at this URL: `{event['previous_sha256']}`.")
        if document["dataset_status"] == "included":
            lines.append("- Dataset: this exact file version is already included; this event adds source provenance.")
        elif document["dataset_status"] == "admitted_elsewhere":
            lines.append(f"- Dataset: these exact bytes are admitted in the `{document['admitted_series']}` series "
                         "(`data/traffic/`), not in the project registry. No project or financial records added by this event.")
        else:
            lines.append("- Dataset: not included. No project or financial records added by this event.")
        if event["pull_request_url"]:
            lines.append(f"- [Discovery pull request]({event['pull_request_url']}).")
        lines.append("")
    if not catalog["events"]:
        lines.extend(["No discovery events recorded yet.", ""])
    lines.append(END)
    return prefix + "\n".join(lines) + suffix
