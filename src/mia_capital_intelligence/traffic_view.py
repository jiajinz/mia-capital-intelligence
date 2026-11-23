"""Admitted monthly MIA traffic series, year-on-year comparison, and Plotly charts for the Traffic tab.

Values are integers taken exactly from the admitted files in data/traffic. Percent changes are
Decimal. No cross-series join, forecast, or financial value is produced here.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from urllib.parse import unquote, urlsplit

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from mia_capital_intelligence.estimate_insights import (
    PALETTE_BAR, PALETTE_INK, PALETTE_LINE, PALETTE_SECONDARY, apply_chart_theme,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "traffic"
CAPACITY_FILE = "traffic_capacity.v1.json"
FIRST_PERIOD = "2010-01"
LAST_PERIOD = "2026-09"
COMBINED_TOTALS = "COMBINED TOTALS"
PASSENGERS = "PASSENGERS"
CARGO_TONS = "TOTAL CARGO-TONS"
SEATS = "SEATS"
AIRCRAFT_MOVEMENTS = "COMMERCIAL AIRCRAFT MVMT"
MONTHLY_MEASURES = {PASSENGERS: "passengers", CARGO_TONS: "cargo_tons"}
CAPACITY_MEASURES = {SEATS: "seats", AIRCRAFT_MOVEMENTS: "commercial_movements"}
PANDEMIC_START = "2020-03"
# Exclusive end of the shaded band (March 2020 to December 2021), so December 2021 is covered.
PANDEMIC_SHADE_END = "2022-01-01"
# Monthly chart x-axis: half a month of padding either side of the first and last reported months.
TRAFFIC_X_START = "2009-12-15"
TRAFFIC_X_END = "2026-10-15"
MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
PERIOD = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
PRIOR_YEAR_TEXT = re.compile(r"same_month_prior_year column of the (\d{4}-\d{2}) report")


@dataclass(frozen=True)
class SourceValue:
    """One admitted integer value with the document, page, and revision evidence that produced it."""

    value: int
    dataset_file: str
    source_file: str
    pdf_page: int | None
    revised: bool
    note: str


@dataclass(frozen=True)
class TrafficMonth:
    period: str
    passengers: SourceValue
    cargo_tons: SourceValue
    seats: SourceValue
    commercial_movements: SourceValue

    @property
    def year(self) -> int:
        return int(self.period[:4])

    @property
    def month(self) -> int:
        return int(self.period[5:])


@dataclass(frozen=True)
class UnavailableMonth:
    """A month inside the series range with no admitted value: a gap, or a month held by a check."""

    period: str
    status: str  # "gap" or "held"
    reason: str


@dataclass(frozen=True)
class TrafficSeries:
    months: tuple[TrafficMonth, ...]
    unavailable: tuple[UnavailableMonth, ...]

    def by_period(self) -> dict[str, TrafficMonth]:
        return {month.period: month for month in self.months}

    def all_periods(self) -> tuple[str, ...]:
        return tuple(sorted({*(m.period for m in self.months), *(u.period for u in self.unavailable)}))


@dataclass(frozen=True)
class YearChange:
    month: int
    current: int | None
    prior: int | None
    change: int | None
    percent: Decimal | None


def expected_periods() -> tuple[str, ...]:
    periods = []
    year, month = int(FIRST_PERIOD[:4]), int(FIRST_PERIOD[5:])
    while f"{year:04d}-{month:02d}" <= LAST_PERIOD:
        periods.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return tuple(periods)


def _file_name(url: str) -> str:
    return unquote(urlsplit(url).path.rsplit("/", 1)[-1])


def _load_document(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("status") != "admitted" or not isinstance(document.get("rows"), list):
        raise ValueError(f"{path.name} is not an admitted traffic dataset")
    return document


def _source_value(row: dict, dataset_file: str) -> SourceValue:
    value = row["value"]
    if type(value) is not int or value < 0:
        raise ValueError(f"{dataset_file}: {row.get('period')} {row.get('measure')} is not a non-negative integer")
    url = row.get("source_url")
    if not isinstance(url, str) or not url:
        raise ValueError(f"{dataset_file}: {row.get('period')} {row.get('measure')} has no source URL")
    source_file = _file_name(url)
    page_index = row.get("pdf_page_index")
    pdf_page = page_index + 1 if type(page_index) is int else None
    vintage = row.get("vintage") or {}
    revised = vintage.get("revision_stamp_printed") is True or "revised" in source_file.lower()
    notes = []
    if revised:
        first = (vintage.get("first_published") or {}).get("status")
        notes.append("Revised report" + ("; first-published version not obtained" if first == "not_obtained" else ""))
    printed_as = vintage.get("printed_as")
    if isinstance(printed_as, str):
        match = PRIOR_YEAR_TEXT.search(printed_as)
        if match:
            notes.append(f"Prior-year column of the {match.group(1)} report")
    return SourceValue(
        value=value, dataset_file=dataset_file, source_file=source_file, pdf_page=pdf_page,
        revised=revised, note=". ".join(notes),
    )


def load_traffic_series(data_dir: Path = DATA_DIR) -> TrafficSeries:
    """Merge admitted COMBINED TOTALS rows; raise on duplicates, partial months, or out-of-range periods."""
    monthly_paths = sorted(data_dir.glob("traffic_monthly.*.json"))
    capacity_path = data_dir / CAPACITY_FILE
    values: dict[tuple[str, str], SourceValue] = {}
    held: dict[str, list[str]] = {}
    for path in [*monthly_paths, capacity_path]:
        document = _load_document(path)
        allowed = CAPACITY_MEASURES if path == capacity_path else MONTHLY_MEASURES
        for period, reasons in (document.get("held_months") or {}).items():
            held.setdefault(period, []).extend(reasons)
        for row in document["rows"]:
            measure = row.get("measure")
            if row.get("market") != COMBINED_TOTALS or measure not in allowed:
                continue
            if row.get("status") != "admitted":
                raise ValueError(f"{path.name}: {row.get('period')} {measure} is not admitted")
            period = row.get("period")
            if not isinstance(period, str) or not PERIOD.match(period) or not FIRST_PERIOD <= period <= LAST_PERIOD:
                raise ValueError(f"{path.name}: period {period!r} is outside the series")
            key = (period, measure)
            if key in values:
                raise ValueError(f"Duplicate admitted value for {period} {measure}")
            values[key] = _source_value(row, path.name)

    months, unavailable = [], []
    for period in expected_periods():
        found = {measure: values.get((period, measure)) for measure in (*MONTHLY_MEASURES, *CAPACITY_MEASURES)}
        if all(found.values()):
            months.append(TrafficMonth(
                period=period,
                passengers=found[PASSENGERS], cargo_tons=found[CARGO_TONS],
                seats=found[SEATS], commercial_movements=found[AIRCRAFT_MOVEMENTS],
            ))
        elif any(found.values()):
            raise ValueError(f"{period} has only some admitted measures")
        elif period in held:
            unavailable.append(UnavailableMonth(period, "held", "; ".join(held[period])))
        else:
            unavailable.append(UnavailableMonth(period, "gap", "No admitted value in the traffic data files"))
    return TrafficSeries(months=tuple(months), unavailable=tuple(unavailable))


def comparable_years(series: TrafficSeries) -> tuple[int, ...]:
    """Years whose prior year also appears in the series, so a year-on-year comparison is possible."""
    years = {month.year for month in series.months}
    return tuple(sorted(year for year in years if year - 1 in years))


def year_comparison(series: TrafficSeries, year: int, measure: str) -> tuple[YearChange, ...]:
    """Compare each calendar month of a year with the same month of the prior year, exactly."""
    by_period = series.by_period()
    rows = []
    for month in range(1, 13):
        current = by_period.get(f"{year}-{month:02d}")
        prior = by_period.get(f"{year - 1}-{month:02d}")
        current_value = getattr(current, measure).value if current else None
        prior_value = getattr(prior, measure).value if prior else None
        change = percent = None
        if current_value is not None and prior_value is not None:
            change = current_value - prior_value
            if prior_value:
                percent = (Decimal(change) * 100 / Decimal(prior_value)).quantize(Decimal("0.1"), ROUND_HALF_UP)
        rows.append(YearChange(month, current_value, prior_value, change, percent))
    return tuple(rows)


def _label(period: str) -> str:
    return f"{MONTH_NAMES[int(period[5:]) - 1]} {period[:4]}"


def traffic_figure(series: TrafficSeries) -> go.Figure:
    """Two stacked monthly panels with the pandemic break shaded and every gap labelled."""
    by_period = series.by_period()
    unavailable = {item.period: item for item in series.unavailable}
    periods = series.all_periods()
    figure = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.14,
        subplot_titles=("Passenger movements per month", "Cargo tons per month"),
    )
    # Panel titles only (applied before other annotations exist): 16 px titles clip on a 320 px screen.
    figure.update_annotations(font=dict(size=14))
    # Alternate gap label heights so neighbouring labels do not overlap on narrow screens.
    lane = {period: index % 2 for index, period in enumerate(p for p in periods if p in unavailable)}
    for row, measure, name, unit in ((1, "passengers", "Passengers", "Passenger movements"),
                                     (2, "cargo_tons", "Cargo", "Reported tons")):
        xs = [f"{period}-01" for period in periods]
        ys = [getattr(by_period[p], measure).value if p in by_period else None for p in periods]
        hover = [
            (f"{_label(p)}<br>{name}: {getattr(by_period[p], measure).value:,}<br>"
             f"Source: {getattr(by_period[p], measure).source_file}<br>"
             f"PDF page: {getattr(by_period[p], measure).pdf_page or 'HTML page'}")
            if p in by_period else f"{_label(p)}<br>No admitted value"
            for p in periods
        ]
        figure.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines", name=name, line=dict(color=PALETTE_BAR, width=2),
            connectgaps=False, text=hover, hovertemplate="%{text}<extra></extra>", showlegend=row == 1,
        ), row=row, col=1)
        revised = [p for p in periods if p in by_period and getattr(by_period[p], measure).revised]
        if revised:
            figure.add_trace(go.Scatter(
                x=[f"{p}-01" for p in revised],
                y=[getattr(by_period[p], measure).value for p in revised],
                mode="markers", name="Revised report value",
                marker=dict(symbol="diamond-open", size=11, color=PALETTE_INK, line=dict(width=2)),
                text=[f"{_label(p)} · revised report" for p in revised],
                hovertemplate="%{text}<extra></extra>", showlegend=row == 1,
            ), row=row, col=1)
        figure.update_yaxes(title_text=unit, rangemode="tozero", tickformat=",", row=row, col=1)
        figure.add_vrect(
            x0=f"{PANDEMIC_START}-01", x1=PANDEMIC_SHADE_END,
            fillcolor=PALETTE_LINE, opacity=0.7, line_width=0, layer="below", row=row, col=1,
        )
        for period in periods:
            if period in unavailable:
                item = unavailable[period]
                label = ("Gap " if item.status == "gap" else "Held ") + period
                figure.add_vline(
                    x=f"{period}-01", line=dict(color=PALETTE_SECONDARY, dash="dot", width=1.5),
                    row=row, col=1,
                )
                figure.add_annotation(
                    x=f"{period}-01", xref="x", yref=f"{'y' if row == 1 else 'y2'} domain",
                    y=0.02 + 0.10 * lane[period],
                    text=label, showarrow=False, xanchor="left", font=dict(size=11, color=PALETTE_INK),
                    bgcolor="rgba(255,255,255,0.9)",
                )
    # Right-anchored at the end of the shaded band so it stays clear of the left-hand tick labels on a 320 px screen.
    figure.add_annotation(
        x=PANDEMIC_SHADE_END, xref="x", yref="y domain", y=0.99,
        text="Pandemic break, Mar 2020 to Dec 2021", showarrow=False, xanchor="right",
        font=dict(size=11, color=PALETTE_INK), bgcolor="rgba(255,255,255,0.9)",
    )
    figure.update_layout(
        height=640, margin=dict(l=12, r=18, t=60, b=110), hovermode="closest",
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0),
    )
    # Fixed range: the autoscaled axis ran to about 2053 in the 390 px browser check, compressing the data.
    figure.update_xaxes(range=[TRAFFIC_X_START, TRAFFIC_X_END])
    figure.update_xaxes(title_text="Month<br>(each point is one reported month)", tickformat="%b %Y", row=2, col=1)
    figure.update_xaxes(tickformat="%Y", row=1, col=1)
    return apply_chart_theme(figure)


def year_figure(series: TrafficSeries, year: int, measure: str) -> go.Figure:
    """Overlay one year on its prior year for the selected measure, with dashed prior-year line."""
    label = "Passenger movements" if measure == "passengers" else "Reported tons"
    rows = year_comparison(series, year, measure)
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=list(MONTH_NAMES), y=[row.prior for row in rows], mode="lines+markers", name=f"{year - 1}",
        line=dict(color=PALETTE_SECONDARY, dash="dash", width=2),
        marker=dict(symbol="circle-open", size=8, color=PALETTE_SECONDARY), connectgaps=False,
        hovertemplate=f"%{{x}} {year - 1}<br>{label}: %{{y:,}}<extra></extra>",
    ))
    figure.add_trace(go.Scatter(
        x=list(MONTH_NAMES), y=[row.current for row in rows], mode="lines+markers", name=f"{year}",
        line=dict(color=PALETTE_BAR, width=3), marker=dict(symbol="circle", size=8, color=PALETTE_BAR),
        connectgaps=False, hovertemplate=f"%{{x}} {year}<br>{label}: %{{y:,}}<extra></extra>",
    ))
    figure.update_layout(
        height=380, margin=dict(l=12, r=18, t=20, b=40),
        xaxis=dict(title="Calendar month"), yaxis=dict(title=label, rangemode="tozero", tickformat=","),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return apply_chart_theme(figure)


def series_years(series: TrafficSeries) -> tuple[int, ...]:
    """Every calendar year that has at least one admitted month, oldest first."""
    return tuple(sorted({month.year for month in series.months}))


def _measure_value(month: TrafficMonth, measure: str) -> int:
    return month.passengers.value if measure == "passengers" else month.cargo_tons.value


def _year_colour(position: int, count: int) -> str:
    """Blend from a light blue-grey to the palette bar colour; the most recent year is the strongest."""
    light, strong = (0xB9, 0xCD, 0xDD), (0x00, 0x7B, 0xB6)
    fraction = 1.0 if count == 1 else position / (count - 1)
    channels = (round(a + (b - a) * fraction) for a, b in zip(light, strong, strict=True))
    return "#" + "".join(f"{channel:02X}" for channel in channels)


def all_years_figure(series: TrafficSeries, years: tuple[int, ...], measure: str) -> go.Figure:
    """One line per selected year across the calendar months. Gaps and held months stay empty, not zero."""
    label = "Passenger movements" if measure == "passengers" else "Reported tons"
    by_period = series.by_period()
    ordered = tuple(sorted(years))
    figure = go.Figure()
    for position, year in enumerate(ordered):
        values = []
        for month in range(1, 13):
            row = by_period.get(f"{year}-{month:02d}")
            values.append(None if row is None else _measure_value(row, measure))
        colour = _year_colour(position, len(ordered))
        newest = position == len(ordered) - 1
        figure.add_trace(go.Scatter(
            x=list(MONTH_NAMES), y=values, mode="lines+markers", name=str(year),
            line=dict(color=colour, width=3 if newest else 2),
            marker=dict(symbol="circle", size=6, color=colour), connectgaps=False,
            hovertemplate=f"%{{x}} {year}<br>{label}: %{{y:,}}<extra></extra>",
        ))
    figure.update_layout(
        height=380, margin=dict(l=12, r=18, t=20, b=40),
        xaxis=dict(title="Calendar month"), yaxis=dict(title=label, rangemode="tozero", tickformat=","),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return apply_chart_theme(figure)


REFERENCE_MONTHS = 12
ERROR_GROUPS = (
    ("2011 to 2019", 2011, 2019),
    ("2020 to 2021, pandemic period", 2020, 2021),
    ("2022 to 2026", 2022, 2026),
)


@dataclass(frozen=True)
class ReferenceMonth:
    """One month of the reference forecast: the same month of the prior year, copied exactly."""

    period: str
    value: int | None
    source_period: str


@dataclass(frozen=True)
class ReferenceError:
    """Mean absolute percentage error of the reference over past months that have both values."""

    label: str
    months: int
    mape: Decimal | None


def shift_period(period: str, months: int) -> str:
    year, month = int(period[:4]), int(period[5:7])
    index = year * 12 + (month - 1) + months
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def _measure_value(month: TrafficMonth, measure: str) -> int:
    return month.passengers.value if measure == "passengers" else month.cargo_tons.value


def reference_forecast(series: TrafficSeries, measure: str) -> tuple[ReferenceMonth, ...]:
    """Reference for the months after the last admitted month: the same month of the prior year, 12 months ahead.

    The reference uses values at least 12 months old, so its inputs are not affected by publication timing.
    """
    by_period = series.by_period()
    rows = []
    for step in range(1, REFERENCE_MONTHS + 1):
        period = shift_period(LAST_PERIOD, step)
        source = shift_period(period, -12)
        prior = by_period.get(source)
        rows.append(ReferenceMonth(period, None if prior is None else _measure_value(prior, measure), source))
    return tuple(rows)


def reference_errors(series: TrafficSeries, measure: str) -> tuple[ReferenceError, ...]:
    """Mean absolute percentage error of the same-month-last-year reference, exact Decimal arithmetic."""
    by_period = series.by_period()
    errors: dict[str, list[Decimal]] = {label: [] for label, _, _ in ERROR_GROUPS}
    for period, month in by_period.items():
        prior = by_period.get(shift_period(period, -12))
        actual = _measure_value(month, measure)
        if prior is None or actual == 0:
            continue
        percent = Decimal(abs(actual - _measure_value(prior, measure))) * 100 / Decimal(actual)
        for label, first, last in ERROR_GROUPS:
            if first <= month.year <= last:
                errors[label].append(percent)
    result = []
    for label, _, _ in ERROR_GROUPS:
        values = errors[label]
        mape = (sum(values, Decimal(0)) / len(values)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP) if values else None
        result.append(ReferenceError(label, len(values), mape))
    return tuple(result)


def reference_figure(series: TrafficSeries, measure: str) -> go.Figure:
    """Last 24 admitted months as a solid line, then the 12 reference months as a dashed line."""
    label = "Passenger movements" if measure == "passengers" else "Reported tons"
    by_period = series.by_period()
    actual_periods = [shift_period(LAST_PERIOD, -offset) for offset in range(23, -1, -1)]
    actual_values = [None if by_period.get(p) is None else _measure_value(by_period[p], measure) for p in actual_periods]
    reference = reference_forecast(series, measure)
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=actual_periods, y=actual_values, mode="lines+markers", name="Admitted value",
        line=dict(color=PALETTE_BAR, width=3), marker=dict(size=6, color=PALETTE_BAR), connectgaps=False,
        hovertemplate=f"%{{x}}<br>{label}: %{{y:,}}<extra></extra>",
    ))
    figure.add_trace(go.Scatter(
        x=[row.period for row in reference], y=[row.value for row in reference], mode="lines+markers",
        name="Reference (same month last year)", line=dict(color=PALETTE_SECONDARY, dash="dash", width=2),
        marker=dict(symbol="circle-open", size=6, color=PALETTE_SECONDARY), connectgaps=False,
        hovertemplate=f"%{{x}} reference<br>{label}: %{{y:,}}<extra></extra>",
    ))
    figure.update_layout(
        height=380, margin=dict(l=12, r=18, t=20, b=40),
        xaxis=dict(title="Month"), yaxis=dict(title=label, rangemode="tozero", tickformat=","),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return apply_chart_theme(figure)
