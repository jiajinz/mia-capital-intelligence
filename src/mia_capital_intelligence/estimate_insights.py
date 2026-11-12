"""Single-document discovery queries and a presentation-only Plotly adapter."""

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from textwrap import shorten
from typing import Any, Mapping

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


def estimate_figure(ranking: EstimateRanking) -> go.Figure:
    """Convert only bar geometry to float; hover retains exact USD and evidence keys."""
    rows = ranking.rows
    figure = go.Figure(go.Bar(
        x=[float(row["estimate_usd"] / Decimal("1000000")) for row in rows],
        y=[row["project_id"] for row in rows], orientation="h",
        customdata=[[
            row["source_ref"], row["project_name"], format_usd(row["estimate_usd"]),
            row["pdf_page"],
        ] for row in rows],
        marker_color="#1E6358",
        hovertemplate=("<b>%{y}</b><br>%{customdata[1]}<br>Estimated cost: %{customdata[2]}"
                       "<br>PDF page %{customdata[3]}<extra></extra>"),
    ))
    figure.update_layout(
        height=max(300, 38 * len(rows) + 90),
        margin=dict(l=15, r=25, t=15, b=45),
        xaxis=dict(title="Estimated cost (USD millions)", tickformat=",~f", rangemode="tozero"),
        yaxis=dict(
            title=None, autorange="reversed", type="category", automargin=True,
            tickvals=[row["project_id"] for row in rows],
            ticktext=[
                shorten(CHART_NAMES.get(row["project_id"], row["project_name"]), width=32, placeholder="…")
                for row in rows
            ],
        ),
        clickmode="event+select", dragmode=False,
        font=dict(size=14, color="#152D36"), showlegend=False,
    )
    return figure


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
