"""Keep discovery idempotent, versioned and isolated from public application data."""

import copy
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from mia_capital_intelligence.discovery_catalog import (
    merge_catalogs, observe, read_catalog, render_log, seed_catalog, serialize_catalog, validate_catalog,
)
from mia_capital_intelligence.discovery_scan import scan
from mia_capital_intelligence.discovery_sources import (
    KEYWORD_SEARCH, MONTHLY, MONTHLY_INDEX, QUARTERLY, TRAFFIC_INDEX, ReportLink, Response, inspect_pdf,
)

NOW = datetime(2026, 11, 17, 18, tzinfo=timezone.utc)
PDF_URL = "https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261824.pdf"


def empty_catalog():
    return {"schema_version": 1, "documents": [], "locations": [], "events": []}


def candidate():
    return ReportLink(QUARTERLY, "Fifth Quarterly Report: Infrastructure 241354", PDF_URL, KEYWORD_SEARCH, "PDF", "261824")


@pytest.fixture
def identity(synthetic_pdf):
    return inspect_pdf(synthetic_pdf("Infrastructure 241354 Quarterly Report: 4/01/2026-06/30/2026"), candidate())


def test_seed_covers_both_inventories_without_inventing_dates():
    catalog = seed_catalog(Path(__file__).resolve().parents[1])
    assert {row["matter_id"] for row in catalog["documents"]} == {
        "260526", "261402", "261824", "261147", "261399", "261400",
    }
    assert all(row["first_seen_at"] is None and row["dataset_status"] == "included" for row in catalog["documents"])
    assert catalog["events"] == []


def test_repeat_bytes_do_not_change_catalog_or_log(identity):
    catalog = empty_catalog()
    assert observe(catalog, candidate(), identity, {"etag": '"one"'}, NOW)
    snapshot = copy.deepcopy(catalog)
    log = render_log("# Published baseline\n", catalog)
    assert not observe(catalog, candidate(), identity, {"etag": '"different-header"'}, NOW + timedelta(days=1))
    assert catalog == snapshot
    assert render_log(log, catalog) == log
    assert "not included" in log


def test_same_url_revision_keeps_both_versions_and_prior_hash(identity):
    catalog = empty_catalog()
    observe(catalog, candidate(), identity, {}, NOW)
    revised = replace(identity, sha256="a" * 64)
    observe(catalog, candidate(), revised, {}, NOW + timedelta(days=1))
    validate_catalog(catalog)
    assert len(catalog["documents"]) == 2
    assert catalog["events"][-1]["kind"] == "revised"
    assert catalog["events"][-1]["previous_sha256"] == identity.sha256
    assert catalog["locations"][0]["sha256"] == revised.sha256
    assert all(row["dataset_status"] == "not_included" for row in catalog["documents"])


def test_repeated_rollbacks_remain_separate_dated_events(identity):
    catalog = empty_catalog()
    for index, digest in enumerate([identity.sha256, "a"*64, identity.sha256, "a"*64]):
        observe(catalog, candidate(), replace(identity, sha256=digest), {}, NOW + timedelta(days=index))
    assert len(catalog["documents"]) == 2 and len(catalog["events"]) == 4


def test_same_bytes_new_link_is_a_mirror_not_another_document(identity):
    catalog = empty_catalog()
    observe(catalog, candidate(), identity, {}, NOW)
    alias = replace(candidate(), url="https://www.miami-airport.com/same.pdf")
    observe(catalog, alias, identity, {}, NOW)
    validate_catalog(catalog)
    assert len(catalog["documents"]) == 1 and len(catalog["locations"]) == 2
    assert catalog["events"][-1]["kind"] == "source_linked"


def test_same_period_different_bytes_are_distinct_candidates(identity):
    catalog = empty_catalog()
    observe(catalog, candidate(), identity, {}, NOW)
    observe(catalog, replace(candidate(), url="https://www.miami-airport.com/variant.pdf"), replace(identity, sha256="a"*64), {}, NOW)
    assert len(catalog["documents"]) == 2
    assert all(event["kind"] == "discovered" for event in catalog["events"])


def test_stale_candidate_history_preserves_published_status(identity):
    previous = empty_catalog()
    observe(previous, candidate(), identity, {}, NOW)
    published = copy.deepcopy(previous)
    published["documents"][0]["dataset_status"] = published["documents"][0]["processing_status"] = "included"
    merged = merge_catalogs(published, previous)
    assert merged["documents"][0]["dataset_status"] == "included"
    assert len(merged["events"]) == 1


def test_broken_version_reference_rejected(identity):
    catalog = empty_catalog()
    observe(catalog, candidate(), identity, {}, NOW)
    catalog["locations"][0]["sha256"] = "f"*64
    with pytest.raises(ValueError):
        validate_catalog(catalog)


@pytest.fixture
def scan_root(tmp_path):
    (tmp_path / "data/discovery").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "data/discovery/catalog.json").write_text(serialize_catalog(empty_catalog()))
    (tmp_path / "docs/DATA_UPDATES.md").write_text("# Published baseline\n")
    return tmp_path


class FakeClient:
    def __init__(self, body, *, index_failure=False, pdf_failure=False):
        self.body, self.index_failure, self.pdf_failure = body, index_failure, pdf_failure
        self.requests = []

    def fetch(self, url, **kwargs):
        self.requests.append((url, kwargs))
        if url == MONTHLY_INDEX:
            if self.index_failure:
                raise TimeoutError("monthly source down")
            return Response(url, b'<a href="/July.pdf">Aviation Capital Program Report July 2026</a>', {})
        if url == TRAFFIC_INDEX:
            if self.index_failure:
                raise TimeoutError("traffic source down")
            return Response(url, b'<h2>Year 2026</h2><a href="/traffic/April.pdf">April</a>', {})
        if url == KEYWORD_SEARCH:
            return Response(url, b'1 Records Found <a href="matter.asp?matter=261824">261824</a>', {})
        if "matter.asp" in url:
            return Response(url, f'Infrastructure 241354 <a href="{PDF_URL}">PDF</a>'.encode(), {})
        if self.pdf_failure:
            return Response(url, b"<html>error page</html>", {})
        if "July.pdf" in url:
            raise TimeoutError("controlled monthly PDF failure")
        if kwargs.get("headers", {}).get("If-None-Match"):
            return Response(url, b"", {}, 304)
        return Response(url, self.body, {"etag": '"sample"'})


def test_live_style_scan_writes_only_candidate_bundle(scan_root, synthetic_pdf):
    before = {path.relative_to(scan_root): path.read_bytes() for path in scan_root.rglob("*") if path.is_file()}
    body = synthetic_pdf("Infrastructure 241354 Quarterly Report: 4/01/2026-06/30/2026")
    report = scan(scan_root, scan_root / "tmp/run", client=FakeClient(body), when=NOW)
    assert report["new_events"] == 1 and report["status"] == "partial"
    catalog = read_catalog(scan_root / "tmp/run/catalog.json")
    assert catalog["documents"][0]["dataset_status"] == "not_included"
    for path, content in before.items():
        assert (scan_root / path).read_bytes() == content
    assert len(list((scan_root / "tmp/run/pdfs").glob("*.pdf"))) == 1


def test_unchanged_rescan_keeps_event_and_uses_conditional_download(scan_root, synthetic_pdf):
    body = synthetic_pdf("Infrastructure 241354 Quarterly Report: 4/01/2026-06/30/2026")
    scan(scan_root, scan_root / "tmp/one", client=FakeClient(body), when=NOW)
    previous = read_catalog(scan_root / "tmp/one/catalog.json")
    client = FakeClient(body)
    report = scan(scan_root, scan_root / "tmp/two", client=client, when=NOW + timedelta(days=1), previous=previous)
    assert not report["changed"] and report["new_events"] == 0
    assert (scan_root / "tmp/one/DATA_UPDATES.md").read_bytes() == (scan_root / "tmp/two/DATA_UPDATES.md").read_bytes()
    assert next(options for url, options in client.requests if url == PDF_URL)["headers"]["If-None-Match"] == '"sample"'


@pytest.mark.parametrize("full_check,days", [(True, 1), (False, 5)])
def test_full_hash_check_and_sunday_bypass_cache_headers(scan_root, synthetic_pdf, full_check, days):
    body = synthetic_pdf("Infrastructure 241354 Quarterly Report: 4/01/2026-06/30/2026")
    scan(scan_root, scan_root / "tmp/one", client=FakeClient(body), when=NOW)
    previous = read_catalog(scan_root / "tmp/one/catalog.json")
    client = FakeClient(body)
    scan(scan_root, scan_root / "tmp/two", client=client, when=NOW + timedelta(days=days), previous=previous, full_hash_check=full_check)
    assert next(options for url, options in client.requests if url == PDF_URL)["headers"] == {}


def test_failed_source_keeps_known_versions_and_checks_other_source(scan_root, synthetic_pdf):
    body = synthetic_pdf("Infrastructure 241354 Quarterly Report: 4/01/2026-06/30/2026")
    scan(scan_root, scan_root / "tmp/one", client=FakeClient(body), when=NOW)
    previous = read_catalog(scan_root / "tmp/one/catalog.json")
    report = scan(scan_root, scan_root / "tmp/two", client=FakeClient(body, index_failure=True), when=NOW, previous=previous)
    assert report["errors"] and not report["changed"]
    assert read_catalog(scan_root / "tmp/two/catalog.json") == previous


def test_invalid_pdf_does_not_create_candidate(scan_root, synthetic_pdf):
    report = scan(scan_root, scan_root / "tmp/run", client=FakeClient(b"", pdf_failure=True), when=NOW)
    assert report["errors"] and not report["changed"]
    assert read_catalog(scan_root / "tmp/run/catalog.json")["documents"] == []


def test_new_file_limit_defers_without_hiding_coverage(scan_root, synthetic_pdf):
    body = synthetic_pdf("Infrastructure 241354 Quarterly Report: 4/01/2026-06/30/2026")
    report = scan(scan_root, scan_root / "tmp/run", client=FakeClient(body), when=NOW, max_new_documents=1)
    # The July monthly report and the April traffic candidate both wait for the next batch.
    assert report["new_events"] == 1 and report["deferred_documents"] == 2
    assert report["status"] == "partial" and report["errors"] == []


def test_keyword_failure_uses_agenda_fallback_and_retains_partial_status(scan_root, synthetic_pdf, monkeypatch):
    def fail(*args, **kwargs):
        raise TimeoutError("keyword service down")
    monkeypatch.setattr("mia_capital_intelligence.discovery_scan.quarterly_links", fail)
    monkeypatch.setattr("mia_capital_intelligence.discovery_scan.agenda_links", lambda *args, **kw: [candidate()])
    body = synthetic_pdf("Infrastructure 241354 Quarterly Report: 4/01/2026-06/30/2026")
    report = scan(scan_root, scan_root / "tmp/run", client=FakeClient(body), when=NOW)
    assert report["new_events"] == 1 and report["status"] == "partial"
    assert report["sources"][-1]["status"] == "ok" and "three recent" in report["sources"][-1]["coverage"]
