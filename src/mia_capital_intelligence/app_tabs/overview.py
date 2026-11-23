"""Overview: the first section a visitor sees. Search, service-area tiles and three at-a-glance panels."""

from datetime import date
from html import escape
from pathlib import Path

import streamlit as st

from mia_capital_intelligence.app_tabs.app_common import (
    SECTIONS, open_section, published_traffic, render_estimate_distribution, report_label, report_period,
)
from mia_capital_intelligence.app_tabs.explore import (
    markdown_label, open_projects_range, open_projects_search, open_service_area,
)
from mia_capital_intelligence.app_tabs.spending import render_spending_summary
from mia_capital_intelligence.directory_queries import ESTIMATE_BANDS, format_usd
from mia_capital_intelligence.estimate_insights import largest_estimates, range_records
from mia_capital_intelligence.operations_updates import OPERATING_AREAS, OPERATIONS_MATTER, operations_updates
from mia_capital_intelligence.public_registry import PublicRegistry
from mia_capital_intelligence.traffic_view import MONTH_NAMES, TrafficSeries, year_comparison

OVERVIEW_CSS = """
    <style>
    .st-key-service-tiles button[data-testid^="stBaseButton"] {
      min-height:5rem; justify-content:flex-start; text-align:left; padding:.8rem 1rem; }
    .st-key-service-tiles button[data-testid^="stBaseButton"] p { overflow-wrap:anywhere; }
    .mia-range-list { list-style:none; margin:.25rem 0 0; padding:0; max-width:52rem }
    .mia-range-row { display:grid; grid-template-columns:minmax(0,1fr) auto; column-gap:1rem;
      padding:.5rem 0; border-top:1px solid #DDE3E8; font-size:.9375rem; line-height:1.4; color:#333333 }
    .mia-range-name { overflow-wrap:anywhere }
    .mia-range-meta { grid-column:1; font-size:.8125rem; color:#3F5161 }
    .mia-range-amount { grid-column:2; grid-row:1; text-align:right; font-variant-numeric:tabular-nums }
    </style>
"""
OVERVIEW_RANGE_ALL = "All"
OVERVIEW_RANGE_ROWS = 10


def render_overview(registry: PublicRegistry, reports: dict, latest_report: str, root: Path) -> None:
    st.html(OVERVIEW_CSS)
    st.caption("Explore airport improvements and reported project costs.")
    render_overview_search()
    render_service_areas(registry, reports)
    estimates, spending, traffic = st.columns(3, gap="medium")
    with estimates, st.container(border=True, key="glance-estimates"):
        render_estimate_glance(registry, reports, latest_report)
    with spending, st.container(border=True, key="glance-spending"):
        st.markdown("**Contract spending**")
        render_spending_summary(root)
    with traffic, st.container(border=True, key="glance-traffic"):
        render_traffic_glance()


def search_from_overview() -> None:
    open_projects_search(st.session_state.get("overview_search", ""))


def render_overview_search() -> None:
    with st.form("overview-search", border=False):
        search_column, search_button = st.columns([5, 1], vertical_alignment="bottom")
        with search_column:
            st.text_input(
                "Search projects and reports", placeholder="Concourse D, chiller, X078A, or 261402",
                key="overview_search",
            )
        with search_button:
            st.form_submit_button("Search", type="primary", on_click=search_from_overview, width="stretch")


def render_service_areas(registry: PublicRegistry, reports: dict) -> None:
    st.subheader("Service areas")
    source = reports.get(OPERATIONS_MATTER)
    if source is None:
        st.info("No operations updates in this view.")
        return
    period = report_period(source["period_start"], source["period_end"])
    memo_date = date.fromisoformat(source["memo_date"])
    st.write("Operations updates from the county's quarterly report, grouped by area.")
    st.caption(f"Miami-Dade County · {period} report · Memo dated {memo_date:%b %d, %Y} · "
               f"[Official report]({source['url']})")
    updates = operations_updates(registry)
    with st.container(key="service-tiles"):
        for index, (column, area) in enumerate(zip(st.columns(len(OPERATING_AREAS)), OPERATING_AREAS, strict=True)):
            count = sum(update.area == area for update in updates)
            noun = "project update" if count == 1 else "project updates"
            with column:
                st.button(
                    f"**{area}**  \n{count} {noun}", key=f"area-tile-{index}", width="stretch",
                    on_click=open_service_area, args=(area,),
                )


def render_estimate_glance(registry: PublicRegistry, reports: dict, latest_report: str) -> None:
    source = reports[latest_report]
    ranking = largest_estimates(registry, latest_report, limit=1)
    period = report_period(source["period_start"], source["period_end"])
    st.markdown("**Reported estimates by size**")
    st.caption(f"{period} · All airports · {ranking.snapshot_count} report entries")
    render_estimate_distribution(ranking, source, show_context=False)
    st.caption("Select a range to list its records.")
    choice = st.radio(
        "Reported estimate range", [OVERVIEW_RANGE_ALL, *ESTIMATE_BANDS], key="overview_range", horizontal=True,
        label_visibility="collapsed", format_func=markdown_label,
    )
    band = None if choice == OVERVIEW_RANGE_ALL else choice
    known_count = ranking.matching_count - ranking.missing_count
    total = known_count if band is None else ranking.band_counts[ESTIMATE_BANDS.index(band)]
    render_range_list(registry, source, latest_report, band, total)
    st.button(
        "Show all in Projects", key="overview-show-all", on_click=open_projects_range, args=(latest_report, band),
    )


def render_range_list(registry: PublicRegistry, source: dict, latest_report: str, band: str | None, total: int) -> None:
    """Plain rows for the chosen range. Names are text, not links; the Projects section opens only from the button."""
    rows = range_records(registry, latest_report, band)[:OVERVIEW_RANGE_ROWS]
    if not rows:
        st.caption("No records with a known estimate in this range.")
        return
    shown = f"Showing {len(rows)} of {total} records, largest first." if total > len(rows) else (
        f"{total} records, largest first.")
    st.caption(shown)
    items = "".join(
        '<li class="mia-range-row">'
        f'<span class="mia-range-name">{escape(row["project_name"])}</span>'
        f'<span class="mia-range-amount">{escape(format_usd(row["estimate_usd"]))}</span>'
        f'<span class="mia-range-meta">{escape(report_label(source))}</span>'
        "</li>"
        for row in rows
    )
    st.html(f'<ul class="mia-range-list" aria-label="Projects in this estimate range">{items}</ul>')


def change_text(change: int | None, percent, prior_label: str) -> str | None:
    if change is None:
        return None
    if percent is None:
        return f"{change:+,} vs {prior_label}"
    return f"{change:+,} ({percent:+.1f}%) vs {prior_label}"


def render_traffic_glance() -> None:
    st.markdown("**Monthly traffic**")
    try:
        series: TrafficSeries = published_traffic()
    except (ValueError, OSError, KeyError):
        st.error("The traffic data could not be validated. The Traffic section is unavailable until the data is repaired.")
        return
    latest = series.months[-1]
    label = f"{MONTH_NAMES[latest.month - 1]} {latest.year}"
    prior_label = f"{MONTH_NAMES[latest.month - 1]} {latest.year - 1}"
    passengers = year_comparison(series, latest.year, "passengers")[latest.month - 1]
    cargo = year_comparison(series, latest.year, "cargo_tons")[latest.month - 1]
    st.metric(f"Passenger movements, {label}", f"{passengers.current:,}",
              delta=change_text(passengers.change, passengers.percent, prior_label))
    st.metric(f"Total cargo tons, {label}", f"{cargo.current:,}",
              delta=change_text(cargo.change, cargo.percent, prior_label))
    st.button("See the Traffic section", key="open-traffic", on_click=open_section, args=(SECTIONS[4],))
