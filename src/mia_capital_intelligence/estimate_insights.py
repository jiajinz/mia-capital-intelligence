"""Single-document discovery queries and a presentation-only Plotly adapter."""

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping, Sequence

import plotly.graph_objects as go

from mia_capital_intelligence.directory_queries import (
    ESTIMATE_BANDS, DirectoryFilters, estimate_band, format_usd, search_records,
)
from mia_capital_intelligence.public_registry import PublicRegistry

CHART_NAMES = {
    "T180B": "Concourse D west extension",
    "V008B": "Concourse F modernization",
    "X078A": "South Terminal east expansion",
    "BA061A": "Central Terminal redevelopment · Phase 1",
    "V008C": "Central Terminal redevelopment · Phase 2",
}
# Display-only: at 320 CSS px the chart plot is about 220 px wide, so bar labels are capped
# at 16 characters including the ellipsis. Hover and the selected record keep the full name.
CHART_LABEL_MAX_CHARS = 16
ESTIMATE_AXIS_TITLE = "Estimated cost (USD millions)"


@dataclass(frozen=True)
class EstimateRanking:
    """Explicit denominators; rows remain document-scoped observations."""

    matter_id: str
    snapshot_count: int
    matching_count: int
    missing_count: int
    rows: tuple[dict[str, Any], ...]
    band_counts: tuple[int, ...]


def largest_estimates(
    registry: PublicRegistry, matter_id: str, airport: str | None = None,
    search: str = "", limit: int = 10,
) -> EstimateRanking:
    """Rank one indexed report with Decimal SQL ordering, never cross-report totals."""
    source = next((row for row in registry.catalog if row["matter_id"] == matter_id), None)
    if source is None or not source["indexed_record_count"]:
        raise ValueError("Choose one indexed infrastructure report")
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("Ranking limit must be an integer from 1 to 20")
    results = search_records(registry, DirectoryFilters(
        search, airport, matter_id, "Reported estimate, highest first",
    ))
    known = [row for row in results if row["estimate_usd"] is not None]
    counts = Counter(estimate_band(row["estimate_usd"]) for row in known)
    return EstimateRanking(
        matter_id, source["indexed_record_count"], len(results), len(results) - len(known),
        tuple(known[:limit]), tuple(counts[band] for band in ESTIMATE_BANDS),
    )


# Public-site palette (recorded in docs/DECISIONS.md D027). Neutral hairlines are derived locally.
PALETTE_INK = "#333333"
PALETTE_SECONDARY = "#3F5161"
PALETTE_LINE = "#DDE3E8"
PALETTE_SURFACE = "#FFFFFF"
PALETTE_BAR = "#007BB6"
PALETTE_ACCENT = "#012851"


def apply_chart_theme(figure: go.Figure) -> go.Figure:
    """Apply the public-site chart palette: dark ink, hairline axes, white surface."""
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=PALETTE_INK),
        hoverlabel=dict(bgcolor=PALETTE_SURFACE, bordercolor=PALETTE_LINE, font=dict(color=PALETTE_INK)),
    )
    for axis in (figure.layout.xaxis, figure.layout.yaxis):
        axis.update(
            gridcolor=PALETTE_LINE, zerolinecolor=PALETTE_LINE, linecolor=PALETTE_LINE,
            tickfont=dict(color=PALETTE_SECONDARY), title_font=dict(color=PALETTE_SECONDARY),
        )
    return figure


def chart_label(name: str, max_chars: int = CHART_LABEL_MAX_CHARS) -> str:
    """Truncate a display label with an ellipsis; the underlying data is never changed."""
    if len(name) <= max_chars:
        return name
    return name[:max_chars - 1].rstrip() + "…"


def chart_labels(rows: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    """Display labels for one chart, in ranking order, that are distinct within the chart.

    A name that would appear more than once after truncation gets a display-only suffix,
    " · N", where N is its 1-based ranking position. The stem is shortened so the whole
    label stays within CHART_LABEL_MAX_CHARS. Rows that are already distinct are unchanged.
    """
    names = [CHART_NAMES.get(row["project_id"], row["project_name"]) for row in rows]
    plain = [chart_label(name) for name in names]
    counts = Counter(plain)
    labels = []
    for position, (name, label) in enumerate(zip(names, plain), start=1):
        if counts[label] == 1:
            labels.append(label)
            continue
        suffix = f" · {position}"
        labels.append(chart_label(name, CHART_LABEL_MAX_CHARS - len(suffix)) + suffix)
    return tuple(labels)


def estimate_figure(ranking: EstimateRanking) -> go.Figure:
    """Convert only bar geometry to float; hover retains exact USD and evidence keys.

    The axis title is shown below the chart by the app, not inside the plot: Plotly centers
    an axis title on the plot area, which clips it when the plot is narrow.
    """
    rows = ranking.rows
    figure = go.Figure(go.Bar(
        x=[float(row["estimate_usd"] / Decimal("1000000")) for row in rows],
        y=[row["project_id"] for row in rows], orientation="h",
        customdata=[[
            row["source_ref"], row["project_name"], format_usd(row["estimate_usd"]),
            row["pdf_page"],
        ] for row in rows],
        marker=dict(color=PALETTE_BAR),
        selected=dict(marker=dict(color=PALETTE_ACCENT)),
        hovertemplate=("<b>%{y}</b><br>%{customdata[1]}<br>Estimated cost: %{customdata[2]}"
                       "<br>PDF page %{customdata[3]}<extra></extra>"),
    ))
    figure.update_layout(
        height=max(300, 38 * len(rows) + 90),
        margin=dict(l=15, r=25, t=15, b=45),
        xaxis=dict(tickformat=",~f", rangemode="tozero"),
        yaxis=dict(
            title=None, autorange="reversed", type="category", automargin=True,
            tickvals=[row["project_id"] for row in rows],
            ticktext=list(chart_labels(rows)),
        ),
        clickmode="event+select", dragmode=False,
        font=dict(size=14, color=PALETTE_INK), showlegend=False,
    )
    return apply_chart_theme(figure)


def selected_source_ref(event: Mapping[str, Any], ranking: EstimateRanking) -> str | None:
    """Accept only a single point whose immutable reference belongs to this ranking."""
    points = event.get("selection", {}).get("points", [])
    if len(points) != 1:
        return None
    custom = points[0].get("customdata")
    if not isinstance(custom, (list, tuple)) or not custom:
        return None
    reference = custom[0]
    return reference if reference in {row["source_ref"] for row in ranking.rows} else None
