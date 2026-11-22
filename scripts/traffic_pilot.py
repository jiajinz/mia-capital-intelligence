"""Collect and inspect candidate MIA calendar-month traffic tables locally.

Run fetch, extract, then verify with the same --folder. Fetch uses the official
index. The other steps work offline on pinned PDF bytes. review.json records
withheld periods and fields; candidate.json retains raw values for inspection.
No command writes application inputs. A rejected period returns exit code 2.
"""
from __future__ import annotations

import argparse
import calendar
from contextlib import contextmanager
import fcntl
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pdfminer
import pdfplumber
from mia_capital_intelligence import traffic_pilot as traffic
from mia_capital_intelligence.discovery_sources import OfficialClient, Page, official_url

INDEX = "https://www.miami-airport.com/airport_stats.asp"
PERIODS = sorted({f"{year:04}-{month:02}" for year in (2024, 2025, 2026)
                  for month in range(1, 10 if year == 2026 else 13)}
                 | {f"{year}-04" for year in range(2019, 2023)})


def write_file(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as file:
        file.write(body)
    Path(file.name).replace(path)


def write_json(path: Path, value: object) -> None:
    write_file(path, (json.dumps(value, indent=2) + "\n").encode())


@contextmanager
def pilot_lock(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def acquire(folder: Path) -> None:
    client = OfficialClient()
    index = client.fetch(INDEX)
    parts = re.split(rb"Year\s*(20\d{2})", index.body)
    urls = {}
    for year, section in zip(parts[1::2], parts[2::2]):
        for href, label in Page(section).links:
            if label.title() not in {*calendar.month_abbr[1:], *calendar.month_name[1:]}:
                continue
            month = list(calendar.month_abbr).index(label[:3].title())
            period = f"{year.decode()}-{month:02}"
            if period in PERIODS and href.lower().endswith(".pdf"):
                url = official_url(href, INDEX)
                if period in urls and urls[period] != url:
                    raise ValueError(f"Conflicting index URLs for {period}")
                urls[period] = url
    if set(urls) != set(PERIODS):
        raise ValueError(f"Missing index periods: {set(PERIODS) - set(urls)}")
    manifest = {}
    for period in PERIODS:
        response = client.fetch(urls[period], max_bytes=5_000_000)
        if not response.body.startswith(b"%PDF-"):
            raise ValueError(f"Expected PDF for {period}")
        digest = hashlib.sha256(response.body).hexdigest()
        write_file(folder / "pdfs" / f"{digest}.pdf", response.body)
        manifest[period] = dict(url=response.url, listed_url=urls[period], sha256=digest,
                                retrieved_at=datetime.now(UTC).isoformat())
    write_json(folder / "sources.json", manifest)


def extraction_key(source: dict, period: str) -> str:
    code = Path(traffic.__file__).read_bytes()
    version = b"|".join([code, pdfplumber.__version__.encode(), pdfminer.__version__.encode(),
                         period.encode(), source["sha256"].encode()])
    return hashlib.sha256(version).hexdigest()


def run_pilot(folder: Path) -> dict:
    sources = json.loads((folder / "sources.json").read_text())
    if set(sources) != set(PERIODS):
        raise ValueError("Source manifest does not cover the configured pilot")
    snapshot = folder / "candidate.json"
    previous = json.loads(snapshot.read_text()) if snapshot.exists() else {}
    periods, issues, revisions = {}, {}, {}
    reused = 0
    for period in PERIODS:
        source = sources[period]
        digest = source["sha256"]
        if not re.fullmatch("[0-9a-f]{64}", digest):
            raise ValueError(f"{period}: invalid PDF digest")
        cache = folder / "cache" / (extraction_key(source, period) + ".json")
        old = previous.get(period, {})
        try:
            body = (folder / "pdfs" / (digest + ".pdf")).read_bytes()
            if hashlib.sha256(body).hexdigest() != digest:
                raise ValueError("PDF digest mismatch")
            if cache.exists():
                saved = json.loads(cache.read_text())
                payload = saved["payload"]
                if hashlib.sha256(payload.encode()).hexdigest() != saved["checksum"]:
                    raise ValueError("Invalid cached result")
                result = json.loads(payload)
                reused += 1
            else:
                try:
                    result = {"rows": traffic.read_page(body, period)}
                except ValueError as error:
                    result = {"error": str(error)}
                payload = json.dumps(result)
                write_json(cache, dict(payload=payload, checksum=hashlib.sha256(payload.encode()).hexdigest()))
            if "error" in result:
                raise ValueError(result["error"])
            entry = dict(source=source, period=period, page_label=None, status="candidate",
                         period_end=f"{period}-{calendar.monthrange(*map(int, period.split('-')))[1]:02}",
                         listed_at=INDEX, publication_date=None,
                         transform="Printed monthly TOTAL; remove grouping commas; parse integer",
                         rows=result["rows"])
            if old and old["source"]["sha256"] != digest:
                revisions[period] = revised_fields(old, entry)
            periods[period] = entry
        except (ValueError, KeyError, OSError) as error:
            issues[period] = dict(source=source, error=str(error), pdf_page_index=0,
                                  previous_digest=old.get("source", {}).get("sha256"))
    field_holds = {p: sorted({field for row in item["rows"] for field in row["held_fields"]})
                   for p, item in periods.items() if any(r["held_fields"] for r in item["rows"])}
    report = dict(field_holds=field_holds, requested=len(sources), extracted=len(periods), cache_hits=reused,
                  rows=sum(len(p["rows"]) for p in periods.values()), held=issues, revisions=revisions)
    # Keep both the immutable previous candidate and the latest review inventory.
    bundle = json.dumps(periods, sort_keys=True).encode()
    archive = folder / "snapshots" / (hashlib.sha256(bundle).hexdigest() + ".json")
    if not archive.exists():
        write_file(archive, bundle)
    if revisions:
        write_json(folder / "revisions" / (hashlib.sha256(bundle).hexdigest() + ".json"), revisions)
    write_json(snapshot, periods)
    write_json(folder / "review.json", report)
    return report


def revised_fields(previous: dict, current: dict) -> dict:
    prior = {(r["market"], r["measure"]): r for r in previous["rows"]}
    changes = []
    for row in current["rows"]:
        before = prior[row["market"], row["measure"]]
        for key, value in row["raw"].items():
            if before["raw"][key] != value:
                changes.append(dict(market=row["market"], measure=row["measure"], column=key,
                                    before=before["raw"][key], after=value))
    year, month = map(int, current["period"].split("-"))
    monthly = any(c["column"] == "month_total" for c in changes)
    return dict(old_sha256=previous["source"]["sha256"], new_sha256=current["source"]["sha256"],
                changes=changes, monthly_outputs_to_recheck=(
                    [current["period"], f"YoY {year+1}-{month:02}", f"FY{year+int(month>=10)}",
                     "forecast runs using this month as training data or an observed outcome"]
                    if monthly else []))


def verify_targets(folder: Path) -> int:
    """Cross-check the two forecast targets with PDFium's independent text reader."""
    import pypdfium2 as pdfium

    periods = json.loads((folder / "candidate.json").read_text())
    sources = json.loads((folder / "sources.json").read_text())
    if set(periods) != set(PERIODS):
        raise ValueError("Target verification requires all configured months")
    checked = 0
    for period, record in periods.items():
        digest = sources[period]["sha256"]
        if record["source"]["sha256"] != digest:
            raise ValueError(f"{period}: stale candidate")
        body = (folder / "pdfs" / (digest + ".pdf")).read_bytes()
        if hashlib.sha256(body).hexdigest() != digest:
            raise ValueError(f"{period}: original PDF digest mismatch")
        with pdfium.PdfDocument(body) as document:
            page = document[0]
            text_page = page.get_textpage()
            text = text_page.get_text_bounded()
            text_page.close()
            page.close()
        section = text.split("COMBINED TOTALS DEPLANED ENPLANED TOTAL")
        if len(section) != 2:
            raise ValueError(f"{period}: ambiguous PDFium combined table")
        for label in ("PASSENGERS", "TOTAL CARGO-TONS"):
            values = re.findall(rf"^{label} +[\d,]+ +[\d,]+ +([\d,]+) ", section[1], re.M)
            expected = [r["value"] for r in record["rows"]
                        if r["measure"] == label and r["market"] == "COMBINED TOTALS"]
            if len(values) != 1 or expected != [traffic.cell_count(values[0])]:
                raise ValueError(f"{period}: PDFium mismatch for {label}")
            checked += 1
    return checked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["fetch", "extract", "verify"])
    parser.add_argument("--folder", type=Path, default=ROOT / "tmp" / "traffic-pilot")
    args = parser.parse_args()
    if args.action == "fetch":
        with pilot_lock(args.folder):
            acquire(args.folder)
        print(f"Collected {len(PERIODS)} candidate periods.")
    elif args.action == "verify":
        with pilot_lock(args.folder):
            checked = verify_targets(args.folder)
        print(f"PDFium matched {checked} monthly passenger and cargo totals.")
    else:
        with pilot_lock(args.folder):
            report = run_pilot(args.folder)
        print(f"candidate {report['extracted']}/{report['requested']} periods | rows={report['rows']} "
              f"| cached={report['cache_hits']} | held={','.join(report['held']) or 'none'} "
              f"| revisions={len(report['revisions'])} | field_holds={list(report['field_holds'])}")
        if report["held"]:
            for period, issue in report["held"].items():
                print(f"{period} | PDF page 1 | {issue['error']} | {issue['source']['url']}")
            sys.exit(2)


if __name__ == "__main__":
    main()
