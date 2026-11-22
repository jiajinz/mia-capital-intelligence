"""Extract candidate monthly MIA traffic observations from the calendar traffic table."""
from __future__ import annotations

import calendar
import io
import re
from operator import itemgetter

import pdfplumber
from pdfplumber.utils import cluster_objects

MARKETS = ("INTERNATIONAL", "DOMESTIC", "COMBINED TOTALS")
MEASURES = {
    "PASSENGERS": "passenger movements",
    "FREIGHT-TONS": "reported tons",
    "MAIL-TONS": "reported tons",
    "TOTAL CARGO-TONS": "reported tons",
    "COMMERCIAL AIRCRAFT MVMT": "commercial aircraft movements",
    "SEATS": "seats",
}
COLUMNS = ("deplaned", "enplaned", "month_total", "same_month_prior_year",
           "month_yoy_pct", "cytd", "prior_cytd", "cytd_yoy_pct")
COUNT = re.compile(r"(?:\d+|\d{1,3}(?:,\d{3})+)")


def cell_count(raw: str) -> int:
    if not COUNT.fullmatch(raw):
        raise ValueError(f"Unexpected count cell {raw!r}")
    return int(raw.replace(",", ""))


def read_page(body: bytes, period: str) -> list[dict]:
    with pdfplumber.open(io.BytesIO(body)) as pdf:
        if len(pdf.pages) != 1:
            raise ValueError("Expected a one-page traffic report")
        words = pdf.pages[0].extract_words()
    # Group each printed baseline and keep coordinates for independent column binding.
    lines = []
    for line in cluster_objects(words, itemgetter("top"), tolerance=2):
        cells = sorted(line, key=itemgetter("x0"))
        lines.append((" ".join(w["text"] for w in cells), cells))
    return extract_rows(lines, period)


def extract_rows(lines: list, period: str) -> list[dict]:
    year, month = map(int, period.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    evidence = {text.replace(",", ", ").replace("  ", " ") for text, _ in lines}
    month_name = calendar.month_name[month].upper()
    # Printed month-end must name the right month and year. A printed day that differs from the
    # calendar is kept as printed and recorded, not silently corrected (e.g. leap-year February).
    printed = [m for text in evidence for m in [re.fullmatch(rf"MONTH ENDED: {month_name} (\d{{1,2}}), {year}", text)] if m]
    if not printed or "MIAMI INTERNATIONAL AIRPORT - TRAFFIC REPORT" not in evidence:
        raise ValueError(f"Airport or printed month-end does not match {period}")
    printed_day = int(printed[0][1])
    ended = f"MONTH ENDED: {month_name} {printed_day}, {year}"
    month_end_note = None if printed_day == last_day else f"printed month-end {printed_day} differs from calendar {last_day}"
    stamp = f"{calendar.month_abbr[month].upper()} {str(year-1)[-2:]}"
    # Some 2017 to 2019 layouts omit the trailing CYTD label after the prior-year column.
    header_pattern = rf"DEPLANED ENPLANED TOTAL {stamp} {stamp} CYTD CYTD (\d{{4}})( CYTD)?$"
    rows = {}
    prior_line = ""
    current = ""
    headers = []
    seen = []
    for text, cells in lines:
        above, prior_line = prior_line, text
        market = next((m for m in MARKETS if text.startswith(m)), None)
        if market:
            tail = re.search(header_pattern, text)
            if above != f"% CHG OVR {year} {year - 1} % CHG OVR" or tail is None:
                raise ValueError(f"{period} {market}: unexpected monthly / CYTD header: {text}")
            footer_year = int(tail[1])
            current = market
            seen.append(market)
            headers = cells[next(i for i, word in enumerate(cells) if word["text"] == "DEPLANED"):]
            header = text
            continue
        if text.startswith("AIRCRAFT OPERATIONS"):
            break
        label = next((m for m in MEASURES if text.startswith(m + " ")), None)
        if not label:
            continue
        key = (current, label)
        if not headers or key in rows:
            raise ValueError(f"{period}: missing header or duplicate {key}")
        numbers = cells[len(label.split()):]
        if len(numbers) != len(COLUMNS):
            raise ValueError(f"{period} {key}: expected eight ordered fields")
        # Compare actual column centers to printed headings. This also works in January,
        # when month and CYTD counts may be numerically identical.
        centers = [(w["x0"] + w["x1"]) / 2 for w in headers]
        target = numbers[2]
        center = (target["x0"] + target["x1"]) / 2
        if not (centers[1] + centers[2]) / 2 < center < (centers[2] + centers[3]) / 2:
            raise ValueError(f"{period} {key}: value outside printed TOTAL column")
        raw = dict(zip(COLUMNS, (w["text"] for w in numbers), strict=True))
        held_fields = ["cytd_yoy_pct"] if footer_year != year - 1 else []
        rows[key] = dict(held_fields=held_fields, market=current, measure=label, unit=MEASURES[label],
                         raw=raw, value=cell_count(raw["month_total"]), table_header=header,
                         period_evidence=ended, month_end_note=month_end_note, pdf_page_index=0,
                         row_y=round(target["top"], 2),
                         total_x=[round(target["x0"], 2), round(target["x1"], 2)])
    if tuple(seen) != MARKETS or set(rows) != {(m, k) for m in MARKETS for k in MEASURES}:
        raise ValueError(f"{period}: incomplete market or measure coverage")
    for (market, measure), row in rows.items():
        raw = row["raw"]
        residual = row["value"] - cell_count(raw["deplaned"]) - cell_count(raw["enplaned"])
        differences = {"directions": residual}
        if market == "COMBINED TOTALS":
            differences["markets"] = row["value"] - sum(rows[m, measure]["value"] for m in MARKETS[:2])
        if measure == "TOTAL CARGO-TONS":
            differences["freight_and_mail"] = row["value"] - sum(
                rows[market, name]["value"] for name in ("FREIGHT-TONS", "MAIL-TONS"))
        row["residuals"] = differences
        tolerance = int(MEASURES[measure] == "reported tons")
        if any(abs(v) > tolerance for v in differences.values()):
            raise ValueError(f"{period} {market} {measure}: reconciliation {differences}")
    return list(rows.values())
