"""Discover official report links and inspect PDF identity and reporting periods."""

from __future__ import annotations

import calendar
import io
import re
import time
from dataclasses import dataclass
from datetime import date, timedelta
from hashlib import sha256
from html.parser import HTMLParser
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

import pdfplumber

MONTHLY_INDEX = "https://www.miami-airport.com/transparency_report.asp"
KEYWORD_SEARCH = "https://www.miamidade.gov/govaction/keywordsearch.asp"
AGENDA_INDEX = "https://www.miamidade.gov/govaction/agendas.asp?Action=Agendas&Oper=DisplayList"
ALLOWED_HOSTS = frozenset({"miami-airport.com", "www.miami-airport.com", "miamidade.gov", "www.miamidade.gov"})
MONTHS = {name.lower(): number for number, name in enumerate(calendar.month_name) if name}
MONTH_PATTERN = "(?:" + "|".join(MONTHS) + ")"
QUARTERLY = "infrastructure_241354"
MONTHLY = "aviation_capital_monthly"


@dataclass(frozen=True)
class ReportLink:
    series: str
    title: str
    url: str
    source_page: str
    link_text: str
    matter_id: str | None = None
    listed_period: str | None = None


@dataclass(frozen=True)
class Response:
    url: str
    body: bytes
    headers: dict[str, str]
    status: int = 200


@dataclass(frozen=True)
class PDFIdentity:
    sha256: str
    size_bytes: int
    page_count: int
    period_start: str | None
    period_end: str | None
    period_evidence: str | None
    period_pdf_page: int | None
    processing_status: str


def official_url(url: str, base: str = "") -> str:
    """Normalize links and reject redirects outside the official HTTPS hosts."""
    parsed = urlsplit(urljoin(base, url.strip()))
    if parsed.scheme not in {"https", "http"} or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("URL must use an approved official host")
    if parsed.username or parsed.password or parsed.port not in {None, 80, 443}:
        raise ValueError("URL must not contain credentials or a custom port")
    # Older county pages publish HTTP links to the same official HTTPS service.
    path = quote(unquote(parsed.path), safe="/()!$&'*,;=:@-._~")
    return urlunsplit(("https", parsed.hostname, path, parsed.query, ""))


class OfficialRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, official_url(newurl, req.full_url))


class OfficialClient:
    """Bound requests, redirects, response sizes, retries and the total scan budget."""

    def __init__(self, *, attempts: int = 3, timeout: float = 30, max_requests: int = 120,
                 max_total_bytes: int = 250 * 1024 * 1024, deadline_seconds: int = 900):
        self.attempts = attempts
        self.timeout = timeout
        self.max_requests = max_requests
        self.max_total_bytes = max_total_bytes
        self.deadline = time.monotonic() + deadline_seconds
        self.requests = 0
        self.bytes = 0
        self.opener = build_opener(OfficialRedirects())

    def fetch(self, url: str, *, data: bytes | None = None,
              headers: dict[str, str] | None = None, max_bytes: int = 50 * 1024 * 1024) -> Response:
        url = official_url(url)
        request_headers = {"User-Agent": "Mozilla/5.0 (compatible; MIA-Capital-Intelligence/1.0)",
                           "Accept-Encoding": "identity", **(headers or {})}
        if data is not None:
            request_headers["Content-Type"] = "application/x-www-form-urlencoded"
        for attempt in range(self.attempts):
            remaining = self.deadline - time.monotonic()
            if self.requests >= self.max_requests or remaining <= 0 or self.bytes >= self.max_total_bytes:
                raise ValueError("Official-source scan budget exhausted")
            self.requests += 1
            try:
                with self.opener.open(Request(url, data=data, headers=request_headers),
                                      timeout=min(self.timeout, remaining)) as response:
                    body = bytearray()
                    while chunk := response.read(min(64 * 1024, max_bytes + 1 - len(body))):
                        self.bytes += len(chunk)
                        body.extend(chunk)
                        if len(body) > max_bytes or self.bytes > self.max_total_bytes:
                            raise ValueError("Official response exceeds the byte limit")
                        if time.monotonic() > self.deadline:
                            raise ValueError("Official-source scan deadline exceeded")
                    return Response(official_url(response.url), bytes(body),
                                    {key.lower(): value for key, value in response.headers.items()}, response.status)
            except HTTPError as error:
                if error.code == 304:
                    return Response(url, b"", {key.lower(): value for key, value in error.headers.items()}, 304)
                if error.code not in {408, 429, 500, 502, 503, 504} or attempt + 1 == self.attempts:
                    raise
            except (URLError, TimeoutError, ConnectionError):
                if attempt + 1 == self.attempts:
                    raise
            time.sleep(min(2 ** attempt, max(0, self.deadline - time.monotonic())))
        raise RuntimeError("No official response")


class Page(HTMLParser):
    """Collect complete anchor text without depending on source whitespace or tags."""

    def __init__(self, body: bytes):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.text: list[str] = []
        self.href: str | None = None
        self.label: list[str] = []
        self.feed(body.decode("utf-8", errors="replace"))

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.label = []

    def handle_data(self, data):
        self.text.append(data)
        if self.href is not None:
            self.label.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.links.append((self.href, " ".join(" ".join(self.label).split())))
            self.href = None


def monthly_links(body: bytes, years: set[int]) -> list[ReportLink]:
    result: dict[str, ReportLink] = {}
    for href, label in Page(body).links:
        if not re.search(r"Aviation\s+Capital\s+Program\s+Report", label, re.I):
            continue
        match = re.search(rf"({MONTH_PATTERN})\s+(20\d{{2}})", label, re.I)
        if not match or int(match[2]) not in years:
            continue
        url = official_url(href, MONTHLY_INDEX)
        if not urlsplit(url).path.lower().endswith(".pdf"):
            continue
        result[url] = ReportLink(MONTHLY, label, url, MONTHLY_INDEX, label,
                                 listed_period=f"{match[2]}-{MONTHS[match[1].lower()]:02}")
    if not result:
        raise ValueError("Monthly index contains no full reports in the requested years")
    return sorted(result.values(), key=lambda link: (link.listed_period or "", link.url), reverse=True)


def quarterly_links(fetch: Callable[..., Response], *, first_year: int, through: date) -> list[ReportLink]:
    """Use the live search form and follow published report-window and PDF links."""
    fields = {"mtintro": f"01-01-{first_year}", "mtintro2": through.strftime("%m-%d-%Y"),
              "mttitle": "241354", "btnSubmit": "Search"}
    response = fetch(KEYWORD_SEARCH, data=urlencode(fields).encode(), max_bytes=5 * 1024 * 1024)
    page = Page(response.body)
    count = re.search(r"(\d+)\s+Records\s+Found", " ".join(page.text), re.I)
    matters = {}
    for href, label in page.links:
        match = re.search(r"(?:\?|&)matter=(\d{6,})\b", href, re.I)
        if match:
            matters[match[1]] = official_url(href, response.url)
    if not count or int(count[1]) != len(matters) or not matters:
        raise ValueError("County search is empty, incomplete or has an unsupported results layout")
    result = []
    errors = []
    for matter, url in matters.items():
        try:
            response = fetch(url, max_bytes=5 * 1024 * 1024)
            page = Page(response.body)
            # The legacy search opens a small JavaScript ReportWindow intermediary.
            if windows := re.findall(r"ReportWindow\(['\"](https?://[^'\"]+)['\"]\)", response.body.decode(errors="replace")):
                if len(windows) != 1:
                    raise ValueError("Ambiguous county report-window link")
                response = fetch(official_url(windows[0]), max_bytes=5 * 1024 * 1024)
                page = Page(response.body)
            text = " ".join(" ".join(page.text).split())
            if not re.search(r"infrastructure", text, re.I) or "241354" not in text:
                raise ValueError(f"Matter {matter} does not identify the infrastructure report series")
            title_match = re.search(r"((?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|\w+)\s+Quarterly\s+Report[^\n]{0,220}?241354)", text, re.I)
            title = title_match[1] if title_match else f"Quarterly infrastructure report — matter {matter}"
            pdfs = {official_url(href, response.url): label for href, label in page.links
                    if re.search(rf"/Matters/Y\d{{4}}/{matter}\.pdf$", urlsplit(href).path, re.I)}
            if len(pdfs) != 1:
                raise ValueError(f"Matter {matter} has no unique published report PDF")
            url, label = next(iter(pdfs.items()))
            result.append(ReportLink(QUARTERLY, title, url, response.url, label, matter))
        except Exception as error:
            errors.append(f"{matter}: {type(error).__name__}: {error}")
    # Preserve successful links even when a different matter page fails.
    if errors:
        raise PartialDiscovery(result, errors)
    return result


class PartialDiscovery(ValueError):
    def __init__(self, links: list[ReportLink], errors: list[str]):
        super().__init__("; ".join(errors))
        self.links = links


class AgendaReports(HTMLParser):
    """Bind each agenda PDF to its own matter and preceding title text."""

    def __init__(self, body: bytes, source_page: str):
        super().__init__(convert_charrefs=True)
        self.source_page = source_page
        self.matter = None
        self.parts = []
        self.reports = {}
        self.feed(body.decode("utf-8", errors="replace"))

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href", "")
        if match := re.search(r"(?:[?&])documentKey=(\d{6,})(?:&|$)", href, re.I):
            self.matter = match[1]
            self.parts = []
        elif match := re.search(r"/Matters/Y\d{4}/(\d{6,})\.pdf$", urlsplit(href).path, re.I):
            text = " ".join(" ".join(self.parts).split())
            if match[1] == self.matter and "241354" in text and re.search("infrastructure", text, re.I):
                url = official_url(href, self.source_page)
                self.reports[url] = ReportLink(QUARTERLY, text[:300], url, self.source_page, "PDF", self.matter)

    def handle_data(self, data):
        if self.matter:
            self.parts.append(data)


def agenda_links(fetch: Callable[..., Response], *, through: date, max_meetings: int = 3) -> list[ReportLink]:
    """Fallback to recently posted BCC agendas using the board's actual form target."""
    response = fetch(AGENDA_INDEX, max_bytes=5 * 1024 * 1024)
    boards = [official_url(href, response.url) for href, label in Page(response.body).links
              if label.strip().lower() == "board of county commissioners"]
    if len(boards) != 1:
        raise ValueError("Agenda index has no unique BCC meeting-list link")
    response = fetch(boards[0], max_bytes=5 * 1024 * 1024)
    text = response.body.decode(errors="replace")
    if not re.search(r'legistarfiles/SourceCode/searchforpdf\.asp\?documentKey=', text, re.I):
        raise ValueError("BCC agenda form target has changed")
    meetings = []
    for match in re.finditer(r'<option\b[^>]*value=["\'](\d+)["\'][^>]*>\s*(\d{1,2}/\d{1,2}/\d{4})', text, re.I):
        month, day, year = map(int, match[2].split("/"))
        meeting_date = date(year, month, day)
        if through - timedelta(days=90) <= meeting_date <= through + timedelta(days=45):
            meetings.append((meeting_date, match[1]))
    if not meetings:
        raise ValueError("BCC agenda list has no recent meetings")
    result, errors = {}, []
    for _, key in sorted(set(meetings), reverse=True)[:max_meetings]:
        # Keys come from real option values, rather than enumerating matter numbers.
        url = official_url(f"legistarfiles/SourceCode/searchforpdf.asp?documentKey={key}&documenttype=agenda", response.url)
        try:
            agenda = fetch(url, max_bytes=5 * 1024 * 1024)
            if not re.search(r"Board of County Commissioners Agenda", " ".join(Page(agenda.body).text), re.I):
                raise ValueError("BCC agenda response is not an agenda")
            result.update(AgendaReports(agenda.body, agenda.url).reports)
        except Exception as error:
            errors.append(f"Agenda {key}: {type(error).__name__}: {error}")
    if errors:
        raise PartialDiscovery(list(result.values()), errors)
    return list(result.values())


def inspect_pdf(body: bytes, link: ReportLink) -> PDFIdentity:
    if not body.startswith(b"%PDF-"):
        raise ValueError("Official download is not a PDF")
    period = None
    with pdfplumber.open(io.BytesIO(body)) as document:
        if not document.pages or len(document.pages) > 500:
            raise ValueError("PDF page count is outside the supported inspection limit")
        page_count = len(document.pages)
        texts = [(number + 1, " ".join((page.extract_text() or "").split()))
                 for number, page in enumerate(document.pages[:6])]
        extracted = " ".join(text for _, text in texts)
        unreadable = not extracted.strip() or len(re.findall(r"\(cid:\d+\)", extracted)) > 50
        if unreadable:
            texts = []
        if link.series == QUARTERLY:
            combined = " ".join(text for _, text in texts)
            if combined and ("241354" not in combined or not re.search("infrastructure", combined, re.I)):
                raise ValueError("PDF does not identify Directive 241354 infrastructure reporting")
            matches = []
            for number, text in texts:
                for match in re.finditer(r"Quarterly\s+Report\s*:\s*(\d{1,2}/\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{1,2}/\d{4})", text, re.I):
                    start = date(*map(int, (match[1].split('/')[2], *match[1].split('/')[:2])))
                    end = date(*map(int, (match[2].split('/')[2], *match[2].split('/')[:2])))
                    matches.append((start, end, match[0], number))
                for match in re.finditer(rf"report\s+covering\s+the\s+months\s+of\s+({MONTH_PATTERN})\s+(?:through|to|[-–])\s+({MONTH_PATTERN})\s+(20\d{{2}})", text, re.I):
                    year = int(match[3]); first = MONTHS[match[1].lower()]; last = MONTHS[match[2].lower()]
                    matches.append((date(year, first, 1), date(year, last, calendar.monthrange(year, last)[1]), match[0], number))
            if matches:
                if len({(start, end) for start, end, _, _ in matches}) != 1:
                    raise ValueError("Conflicting explicit quarterly reporting periods")
                period = matches[0]
                start, end = period[:2]
                if start.month not in {1, 4, 7, 10} or start.day != 1 or end != date(start.year, start.month + 2, calendar.monthrange(start.year, start.month + 2)[1]):
                    raise ValueError("Explicit reporting range is not a complete calendar quarter")
        else:
            matches = []
            for number, text in texts:
                for match in re.finditer(rf"Aviation\s+Capital\s+Program\s+Report\s*[-–—:]?\s*({MONTH_PATTERN})\s*(20\d{{2}})", text, re.I):
                    month, year = MONTHS[match[1].lower()], int(match[2])
                    matches.append((date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1]), match[0], number))
            if matches:
                if len({(start, end) for start, end, _, _ in matches}) != 1:
                    raise ValueError("Conflicting monthly report labels")
                period = matches[0]
                if link.listed_period and period[0].strftime("%Y-%m") != link.listed_period:
                    raise ValueError("PDF report month differs from the official index label")
            elif not any(re.search(r"Aviation\s+Capital\s+Program\s+Report", text, re.I) for _, text in texts):
                # Preserve scanned official reports as candidates with unknown text metadata.
                if any(text for _, text in texts):
                    raise ValueError("PDF does not identify the Aviation Capital Program report series")
    return PDFIdentity(sha256(body).hexdigest(), len(body), page_count,
                       period[0].isoformat() if period else None, period[1].isoformat() if period else None,
                       period[2] if period else None, period[3] if period else None,
                       "candidate" if period else "text_unreadable" if unreadable else "period_unknown")
