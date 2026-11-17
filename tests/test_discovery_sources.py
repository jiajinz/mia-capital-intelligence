"""Official HTML adapters, explicit report periods and bounded downloads."""

from datetime import date
from io import BytesIO
from urllib.error import HTTPError
from urllib.parse import parse_qs

import pytest

from mia_capital_intelligence.discovery_sources import (
    AGENDA_INDEX, KEYWORD_SEARCH, MONTHLY, MONTHLY_INDEX, QUARTERLY, OfficialClient, OfficialRedirects,
    PartialDiscovery, ReportLink, Response, agenda_links, inspect_pdf, monthly_links, official_url, quarterly_links,
)


def link(series=QUARTERLY, **kwargs):
    return ReportLink(series, "Synthetic official report", "https://www.miamidade.gov/sample.pdf",
                      KEYWORD_SEARCH, "PDF", **kwargs)


def test_monthly_index_full_reports_years_and_url_encoding():
    html = b'''<a href="/library/July 2026.pdf">Aviation <b>Capital</b> Program Report July 2026</a>
    <a href="/library/June2024.pdf">Aviation Capital Program Report June 2024</a>
    <a href="/library/Financial.pdf">Financial Status July 2026</a>'''
    result = monthly_links(html, {2025, 2026})
    assert len(result) == 1
    assert result[0].listed_period == "2026-07"
    assert result[0].url == "https://www.miami-airport.com/library/July%202026.pdf"
    assert result[0].source_page == MONTHLY_INDEX


@pytest.mark.parametrize("url", ["https://example.com/x.pdf", "https://www.miamidade.gov.evil.test/x", "file:///tmp/x",
                                      "https://user:password@www.miamidade.gov/x", "https://www.miamidade.gov:8443/x"])
def test_nonofficial_or_credentialed_urls_rejected(url):
    with pytest.raises(ValueError):
        official_url(url)


def test_legacy_http_is_upgraded_and_fragment_removed():
    assert official_url("http://www.miamidade.gov/file.pdf#page=2") == "https://www.miamidade.gov/file.pdf"


def test_redirect_is_checked_before_request_leaves_official_hosts():
    from urllib.request import Request
    with pytest.raises(ValueError):
        OfficialRedirects().redirect_request(Request(KEYWORD_SEARCH), None, 302, "Found", {}, "https://example.com/x")


def test_search_form_report_window_and_pdf_are_followed():
    seen = []
    def fetch(url, **kwargs):
        seen.append((url, kwargs))
        if url == KEYWORD_SEARCH:
            return Response(url, b'1 Records Found <a href="matter.asp?matter=261824">261824</a>', {})
        if "file=true" not in url:
            return Response(url, b'''<a href="javascript:ReportWindow('http://www.miamidade.gov/govaction/matter.asp?matter=261824&file=true');">Open</a>''', {})
        return Response(url, b'''Fifth Quarterly Report: Infrastructure Directive 241354
            <a href="legistarfiles/Matters/Y2026/261824.pdf">Printable PDF Format</a>''', {})
    result = quarterly_links(fetch, first_year=2025, through=date(2026, 11, 17))
    assert len(result) == 1 and result[0].matter_id == "261824"
    assert result[0].url.endswith("/Y2026/261824.pdf")
    assert parse_qs(seen[0][1]["data"].decode()) == {
        "mtintro": ["01-01-2025"], "mtintro2": ["11-17-2026"], "mttitle": ["241354"], "btnSubmit": ["Search"]}
    assert all(url.startswith("https://") for url, _ in seen)


@pytest.mark.parametrize("body", [b"No reports", b"0 Records Found", b'2 Records Found <a href="matter.asp?matter=261824">261824</a>'])
def test_empty_or_truncated_search_is_a_failure(body):
    with pytest.raises(ValueError, match="empty, incomplete"):
        quarterly_links(lambda url, **kw: Response(url, body, {}), first_year=2025, through=date(2026, 11, 17))


def test_failed_matter_preserves_other_successful_links():
    def fetch(url, **kwargs):
        if url == KEYWORD_SEARCH:
            return Response(url, b'2 Records Found <a href="matter.asp?matter=261824">A</a><a href="matter.asp?matter=261402">B</a>', {})
        if "261402" in url:
            raise TimeoutError("source timeout")
        return Response(url, b'Infrastructure 241354 <a href="/govaction/legistarfiles/Matters/Y2026/261824.pdf">PDF</a>', {})
    with pytest.raises(PartialDiscovery) as caught:
        quarterly_links(fetch, first_year=2025, through=date(2026, 11, 17))
    assert [row.matter_id for row in caught.value.links] == ["261824"]


def test_quarter_period_uses_body_not_publication_date(synthetic_pdf):
    body = synthetic_pdf("Date November 17 2026. Infrastructure Directive 241354",
                         "Report covering the months of April through June 2026. Fifth Quarterly Report: 4/01/2026-06/30/2026")
    result = inspect_pdf(body, link())
    assert (result.period_start, result.period_end, result.period_pdf_page) == ("2026-04-01", "2026-06-30", 2)
    assert result.processing_status == "candidate"


def test_month_period_uses_report_label_not_memo_date(synthetic_pdf):
    result = inspect_pdf(synthetic_pdf("Date: September 1 2026. Aviation Capital Program Report - July2026"),
                         link(MONTHLY, listed_period="2026-07"))
    assert (result.period_start, result.period_end) == ("2026-07-01", "2026-07-31")


def test_listing_pdf_period_conflict_fails(synthetic_pdf):
    with pytest.raises(ValueError, match="differs"):
        inspect_pdf(synthetic_pdf("Aviation Capital Program Report - August 2026"), link(MONTHLY, listed_period="2026-07"))


def test_conflicting_quarters_fail(synthetic_pdf):
    with pytest.raises(ValueError, match="Conflicting"):
        inspect_pdf(synthetic_pdf("Infrastructure 241354 Quarterly Report: 4/01/2026-06/30/2026",
                                 "Quarterly Report: 1/01/2026-03/31/2026"), link())


def test_unknown_period_and_scanned_page_preserve_unknown(synthetic_pdf):
    for body, status in ((synthetic_pdf("Infrastructure 241354 Date November 17 2026"), "period_unknown"),
                         (synthetic_pdf(""), "text_unreadable")):
        result = inspect_pdf(body, link())
        assert result.period_start is None and result.processing_status == status


def test_missing_font_mapping_keeps_candidate_period_unknown(synthetic_pdf):
    result = inspect_pdf(synthetic_pdf("Date March 4 2025 " + "(cid:17)" * 60), link(MONTHLY, listed_period="2025-02"))
    assert result.processing_status == "text_unreadable" and result.period_start is None


@pytest.mark.parametrize("body", [b"<html>Service unavailable</html>", b"%PDF-not actually a PDF"])
def test_non_pdf_and_broken_pdf_fail(body):
    with pytest.raises(Exception):
        inspect_pdf(body, link())


def test_http_byte_limit_and_request_budget():
    class Download(BytesIO):
        status = 200
        url = MONTHLY_INDEX
        headers = {}
    class Opener:
        def open(self, *args, **kwargs):
            return Download(b"a" * 20)
    client = OfficialClient(max_requests=1)
    client.opener = Opener()
    with pytest.raises(ValueError, match="byte limit"):
        client.fetch(MONTHLY_INDEX, max_bytes=10)
    with pytest.raises(ValueError, match="budget"):
        client.fetch(MONTHLY_INDEX)


def test_conditional_response_is_returned_without_body():
    class Opener:
        def open(self, *args, **kwargs):
            raise HTTPError(MONTHLY_INDEX, 304, "Not Modified", {}, None)
    client = OfficialClient()
    client.opener = Opener()
    assert client.fetch(MONTHLY_INDEX).status == 304


def test_transient_network_failure_is_retried(monkeypatch):
    class Download(BytesIO):
        status = 200
        url = MONTHLY_INDEX
        headers = {}
    class Opener:
        calls = 0
        def open(self, *args, **kwargs):
            self.calls += 1
            if self.calls < 3:
                raise TimeoutError("temporary")
            return Download(b"ok")
    monkeypatch.setattr("mia_capital_intelligence.discovery_sources.time.sleep", lambda _: None)
    client = OfficialClient()
    client.opener = Opener()
    assert client.fetch(MONTHLY_INDEX).body == b"ok" and client.requests == 3


def test_bcc_fallback_uses_published_meeting_keys_and_matches_own_matter():
    seen = []
    def fetch(url, **kwargs):
        seen.append(url)
        if url == AGENDA_INDEX:
            return Response(url, b'<a href="agendas.asp?Agenda=CC">Board of County Commissioners</a>', {})
        if "Agenda=CC" in url:
            return Response(url, b'''<script>url="legistarfiles/SourceCode/searchforpdf.asp?documentKey="</script>
                <option value="5580">11/17/2026<option value="1111">1/01/2024''', {})
        return Response("https://www.miamidade.gov/govaction/commagenda.asp?cmbmeetdate=5580", b'''
            Board of County Commissioners Agenda
            <a href="legistarfiles/SourceCode/searchforpdf.asp?documenttype=matter&documentKey=261824">261824</a>
            Fifth Quarterly Report: Infrastructure Directive 241354
            <a href="legistarfiles/Matters/Y2026/261824.pdf">PDF</a>
            <a href="legistarfiles/SourceCode/searchforpdf.asp?documenttype=matter&documentKey=261999">261999</a>
            Unrelated agenda item
            <a href="legistarfiles/Matters/Y2026/261999.pdf">PDF</a>''', {})
    result = agenda_links(fetch, through=date(2026, 11, 17))
    assert len(result) == 1 and result[0].matter_id == "261824"
    assert result[0].url == "https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261824.pdf"
    assert any("documentKey=5580" in url for url in seen)
    assert not any("1111" in url for url in seen)


def test_bcc_fallback_empty_meeting_list_is_a_failure():
    def fetch(url, **kwargs):
        if url == AGENDA_INDEX:
            return Response(url, b'<a href="agendas.asp?Agenda=CC">Board of County Commissioners</a>', {})
        return Response(url, b'legistarfiles/SourceCode/searchforpdf.asp?documentKey=', {})
    with pytest.raises(ValueError, match="no recent meetings"):
        agenda_links(fetch, through=date(2026, 11, 17))
