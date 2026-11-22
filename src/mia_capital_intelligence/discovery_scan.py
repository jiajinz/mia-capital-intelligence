"""Run bounded discovery scans without writing application datasets."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mia_capital_intelligence.discovery_catalog import (
    CATALOG_PATH, LOG_PATH, merge_catalogs, observe, read_catalog, render_log, serialize_catalog,
)
from mia_capital_intelligence.discovery_sources import (
    AGENDA_INDEX, KEYWORD_SEARCH, MONTHLY_INDEX, TRAFFIC_INDEX, OfficialClient, PartialDiscovery, ReportLink,
    agenda_links, inspect_pdf, monthly_links, quarterly_links, traffic_links,
)


def scan(root: Path, output: Path, *, client: OfficialClient, when: datetime,
         previous: dict[str, Any] | None = None, max_new_documents: int = 15,
         full_hash_check: bool = False) -> dict[str, Any]:
    if when.utcoffset() is None or max_new_documents < 1:
        raise ValueError("A timezone and positive document limit are required")
    when = when.astimezone(timezone.utc)
    catalog = read_catalog(root / CATALOG_PATH)
    if previous is not None:
        catalog = merge_catalogs(catalog, previous)
    original = copy.deepcopy(catalog)
    years = {when.year - 1, when.year}
    report: dict[str, Any] = {"checked_at": when.isoformat(timespec="seconds"), "years": sorted(years),
                              "sources": [], "errors": [], "checked_documents": 0,
                              "unchanged_documents": 0, "deferred_documents": 0,
                              "changed": False, "new_events": 0}
    links = []
    try:
        response = client.fetch(MONTHLY_INDEX, max_bytes=5 * 1024 * 1024)
        found = monthly_links(response.body, years)
        links.extend(found)
        report["sources"].append({"url": MONTHLY_INDEX, "status": "ok", "reports_found": len(found)})
    except Exception as error:
        report["sources"].append({"url": MONTHLY_INDEX, "status": "failed"})
        report["errors"].append({"url": MONTHLY_INDEX, "stage": "index", "error": f"{type(error).__name__}: {error}"})
    try:
        response = client.fetch(TRAFFIC_INDEX, max_bytes=5 * 1024 * 1024)
        found = traffic_links(response.body, years)
        links.extend(found)
        report["sources"].append({"url": TRAFFIC_INDEX, "status": "ok", "reports_found": len(found)})
    except Exception as error:
        report["sources"].append({"url": TRAFFIC_INDEX, "status": "failed"})
        report["errors"].append({"url": TRAFFIC_INDEX, "stage": "index", "error": f"{type(error).__name__}: {error}"})
    try:
        found = quarterly_links(client.fetch, first_year=min(years), through=when.date())
        links.extend(found)
        report["sources"].append({"url": KEYWORD_SEARCH, "status": "ok", "reports_found": len(found)})
    except Exception as error:
        if isinstance(error, PartialDiscovery):
            links.extend(error.links)
        report["sources"].append({"url": KEYWORD_SEARCH, "status": "failed"})
        report["errors"].append({"url": KEYWORD_SEARCH, "stage": "index", "error": f"{type(error).__name__}: {error}"})
        try:
            fallback = agenda_links(client.fetch, through=when.date())
            links.extend(fallback)
            report["sources"].append({"url": AGENDA_INDEX, "status": "ok", "reports_found": len(fallback),
                                      "coverage": "Up to three recent BCC agendas; keyword search remains incomplete"})
        except Exception as fallback_error:
            if isinstance(fallback_error, PartialDiscovery):
                links.extend(fallback_error.links)
            report["sources"].append({"url": AGENDA_INDEX, "status": "failed"})
            report["errors"].append({"url": AGENDA_INDEX, "stage": "index",
                                      "error": f"{type(fallback_error).__name__}: {fallback_error}"})

    # Revisit known URLs even if an index temporarily drops its historical links.
    versions = {row["sha256"]: row for row in catalog["documents"]}
    locations = {row["url"]: row for row in catalog["locations"]}
    by_url = {link.url: link for link in links}
    for location in catalog["locations"]:
        document = versions[location["sha256"]]
        by_url.setdefault(location["url"], ReportLink(
            document["series"], document["title"], location["url"], location["source_page"],
            location["link_text"], document["matter_id"],
        ))
    # New quarterly reports precede monthly backfill. All known locations are checked.
    ordered = sorted(by_url.values(), key=lambda link: (
        link.url in locations, link.series != "infrastructure_241354",
        -(int((link.listed_period or "0000-00").replace("-", ""))), link.url,
    ))
    new_downloads = 0
    for link in ordered:
        location = locations.get(link.url)
        if location is None and new_downloads >= max_new_documents:
            report["deferred_documents"] += 1
            continue
        if location is None:
            new_downloads += 1
        try:
            headers = {}
            label_matches_version = not (location and link.listed_period and
                versions[location["sha256"]]["period_start"] and
                not versions[location["sha256"]]["period_start"].startswith(link.listed_period))
            if location and label_matches_version and not full_hash_check and when.weekday() != 6:
                if location.get("etag"):
                    headers["If-None-Match"] = location["etag"]
                if location.get("last_modified"):
                    headers["If-Modified-Since"] = location["last_modified"]
            response = client.fetch(link.url, headers=headers)
            report["checked_documents"] += 1
            if response.status == 304:
                if not location or not headers:
                    raise ValueError("Unexpected conditional response without a known PDF version")
                report["unchanged_documents"] += 1
                continue
            identity = inspect_pdf(response.body, link)
            if not location or location["sha256"] != identity.sha256:
                raw = output / "pdfs" / f"{identity.sha256}.pdf"
                raw.parent.mkdir(parents=True, exist_ok=True)
                raw.write_bytes(response.body)
            changed = observe(catalog, link, identity, response.headers, when, resolved_url=response.url)
            if not changed:
                report["unchanged_documents"] += 1
        except Exception as error:
            report["errors"].append({"url": link.url, "stage": "pdf", "error": f"{type(error).__name__}: {error}"})

    report["changed"] = catalog != original
    report["new_events"] = len(catalog["events"]) - len(original["events"])
    report["status"] = "failed" if not report["checked_documents"] else (
        "partial" if report["errors"] or report["deferred_documents"] else "ok"
    )
    output.mkdir(parents=True, exist_ok=True)
    (output / "catalog.json").write_text(serialize_catalog(catalog), encoding="utf-8")
    (output / "DATA_UPDATES.md").write_text(render_log((root / LOG_PATH).read_text(), catalog), encoding="utf-8")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "summary.md").write_text(render_summary(report), encoding="utf-8")
    return report


def render_summary(report: dict[str, Any]) -> str:
    lines = ["## Official report discovery", "", f"Checked: {report['checked_at']}",
             f"Status: {report['status']}", f"PDF locations checked: {report['checked_documents']}",
             f"Unchanged: {report['unchanged_documents']}", f"New discovery events: {report['new_events']}",
             f"New locations deferred to the next batch: {report['deferred_documents']}", ""]
    for source in report["sources"]:
        lines.append(f"- {source['status']}: {source['url']}")
    if report["errors"]:
        lines.extend(["", "### Source errors", ""])
        for error in report["errors"]:
            detail = " ".join(error["error"].split())[:600].replace("`", "'").replace("<", "&lt;")
            lines.append(f"- {error['stage']} · {error['url']}: {detail}")
    return "\n".join(lines) + "\n"
