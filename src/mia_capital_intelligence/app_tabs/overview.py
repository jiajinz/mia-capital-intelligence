"""Overview: the first section a visitor sees. Search, service areas, an estimate range drill-down and three panels."""

from datetime import date
from decimal import Decimal
from html import escape
from pathlib import Path

import streamlit as st

from mia_capital_intelligence.app_tabs.app_common import (
    SECTION_TRAFFIC, open_report, open_section, profile_permalink, published_traffic, render_detail,
    render_estimate_distribution, report_label, report_period,
)
from mia_capital_intelligence.app_tabs.explore import ESTIMATE_SORT, markdown_label
from mia_capital_intelligence.app_tabs.spending import render_spending_summary
from mia_capital_intelligence.directory_queries import (
    ESTIMATE_BANDS, DirectoryFilters, format_usd, search_records,
)
from mia_capital_intelligence.estimate_insights import largest_estimates, range_records
from mia_capital_intelligence.operations_updates import OPERATING_AREAS, OPERATIONS_MATTER, operations_updates
from mia_capital_intelligence.public_registry import PublicRegistry
from mia_capital_intelligence.traffic_view import MONTH_NAMES, TrafficSeries, year_comparison

OVERVIEW_CSS = """
    <style>
    .st-key-service-tiles button[data-testid^="stBaseButton"] {
      min-height:5rem; justify-content:flex-start; text-align:left; padding:.8rem 1rem; }
    .st-key-service-tiles button[data-testid^="stBaseButton"] p { overflow-wrap:anywhere; }
    .st-key-overview-cards button[data-testid^="stBaseButton"] { justify-content:flex-start; text-align:left; }
    .st-key-overview-cards button[data-testid^="stBaseButton"] p { overflow-wrap:anywhere; }
    .mia-drill-row { padding:.5rem 0; border-top:1px solid #DDE3E8; }
    .mia-drill-name { margin:0; font-weight:700; color:#333333; overflow-wrap:anywhere; }
    .mia-drill-meta { margin:0; font-size:.875rem; line-height:1.4; color:#3F5161; }
    </style>
"""
OVERVIEW_RANGE_ALL = "All"


def render_overview(registry: PublicRegistry, reports: dict, latest_report: str, root: Path) -> None:
    st.html(OVERVIEW_CSS)
    st.caption("Explore airport improvements and reported project costs.")
    render_overview_search(registry, reports)
    render_service_areas(registry, reports)
    estimates, spending, traffic = st.columns(3, gap="medium")
    with estimates, st.container(border=True, key="glance-estimates"):
        choice = render_estimate_glance(registry, reports, latest_report)
    with spending, st.container(border=True, key="glance-spending"):
        st.markdown("**Contract spending**")
        render_spending_summary(root)
    with traffic, st.container(border=True, key="glance-traffic"):
        render_traffic_glance()
    if choice is not None:
        render_range_drilldown(registry, reports, latest_report, choice)


def submit_overview_search() -> None:
    st.session_state.update(
        overview_query=st.session_state.get("overview_search", "").strip(), overview_area=None,
    )
    st.session_state.pop("overview_record", None)


def clear_overview_search() -> None:
    st.session_state.update(overview_query="", overview_search="")
    st.session_state.pop("overview_record", None)


def open_service_area(area: str) -> None:
    """Callback for a service tile: show that area's updates below the tiles, on this page."""
    st.session_state.update(overview_area=area, overview_query="", overview_search="")
    st.session_state.pop("overview_record", None)


def select_overview_record(reference: str) -> None:
    st.session_state["overview_record"] = reference


def close_range_drilldown() -> None:
    """Callback for Back to overview: clear the range choice so the sub-dashboard closes."""
    st.session_state["overview_range"] = None


def render_overview_search(registry: PublicRegistry, reports: dict) -> None:
    with st.form("overview-search", border=False):
        search_column, search_button = st.columns([5, 1], vertical_alignment="bottom")
        with search_column:
            st.text_input(
                "Search projects and reports", placeholder="Concourse D, chiller, X078A, or 261402",
                key="overview_search",
            )
        with search_button:
            st.form_submit_button("Search", type="primary", on_click=submit_overview_search, width="stretch")
    query = st.session_state.get("overview_query", "")
    if query:
        render_search_results(registry, reports, query)


def matches_report(source: dict, query: str) -> bool:
    text = f"{report_label(source)} {source['title']}".lower()
    return all(word in text for word in query.lower().split())


def render_search_results(registry: PublicRegistry, reports: dict, query: str) -> None:
    matches = [source for source in reports.values() if matches_report(source, query)]
    records = search_records(registry, DirectoryFilters(query, None, None, ESTIMATE_SORT))
    st.subheader("Search results")
    noun = "source record" if len(records) == 1 else "source records"
    st.caption(f"{len(records)} matching {noun} · {len(reports)} indexed reports")
    if matches:
        st.markdown("**Reports matching this search**")
        for source in matches:
            st.button(
                f"{report_label(source)} · {source['title']}", key=f"report-{source['matter_id']}",
                width="stretch", on_click=open_report, args=(source["matter_id"],),
            )
    if records:
        for row in records:
            render_record_row(row, reports, "search")
    else:
        st.info("No source records match this search. Try a shorter keyword.")
    st.button("Clear search", key="overview-clear-search", on_click=clear_overview_search)


def render_record_row(row: dict, reports: dict, prefix: str) -> None:
    """One project in a list: name, report period and reported estimate, then small links to the PDF and permalink."""
    reference = row["source_ref"]
    source_url = reports[row["matter_id"]]["url"]
    st.html(
        '<div class="mia-drill-row">'
        f'<p class="mia-drill-name">{escape(row["project_name"])}</p>'
        '<p class="mia-drill-meta">'
        f'{escape(report_period(row["period_start"], row["period_end"]))} · '
        f'Reported estimate <span style="white-space:nowrap">{escape(format_usd(row["estimate_usd"]))}</span></p></div>'
    )
    st.caption(
        f"[Open official PDF · page {row['pdf_page']}]({source_url}#page={row['pdf_page']}) · "
        f"[Link to this record]({profile_permalink(reference)})"
    )


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
    if selected_area := st.session_state.get("overview_area"):
        render_service_area(registry, source, selected_area)


def render_service_area(registry: PublicRegistry, source: dict, area: str) -> None:
    updates = [update for update in operations_updates(registry) if update.area == area]
    st.subheader(area)
    noun = "project update" if len(updates) == 1 else "project updates"
    st.caption(f"{len(updates)} {noun} from the county's quarterly report")
    selected = st.session_state.get("overview_record")
    with st.container(key="overview-cards"):
        for update in updates:
            reference = update.source_ref
            with st.container(border=True):
                st.caption(f"{update.area} · {update.project_id}")
                st.markdown(f"**{update.title}**")
                st.write(update.description)
                st.markdown(f"[Read report update]({source['url']}#page={update.memo_page})")
                st.button(
                    "Open project record", key=f"open-{reference}",
                    type="primary" if selected == reference else "secondary",
                    on_click=select_overview_record, args=(reference,),
                )
    if selected in {update.source_ref for update in updates}:
        render_detail(registry, selected)


def render_estimate_glance(registry: PublicRegistry, reports: dict, latest_report: str) -> str | None:
    """Show the estimate distribution and return the range the visitor chose, if any."""
    source = reports[latest_report]
    ranking = largest_estimates(registry, latest_report, limit=1)
    period = report_period(source["period_start"], source["period_end"])
    st.markdown("**Reported estimates by size**")
    st.caption(f"{period} · All airports · {ranking.snapshot_count} report entries")
    render_estimate_distribution(ranking, source, show_context=False)
    st.caption("Select a range to list its records.")
    return st.radio(
        "Reported estimate range", [OVERVIEW_RANGE_ALL, *ESTIMATE_BANDS], key="overview_range", index=None,
        horizontal=True, label_visibility="collapsed", format_func=markdown_label,
    )


def render_range_drilldown(registry: PublicRegistry, reports: dict, latest_report: str, choice: str) -> None:
    """Sub-dashboard for one estimate range. It opens inside the Overview; the section does not change."""
    band = None if choice == OVERVIEW_RANGE_ALL else choice
    rows = range_records(registry, latest_report, band)
    total = sum((row["estimate_usd"] for row in rows), Decimal("0"))
    source = reports[latest_report]
    period = report_period(source["period_start"], source["period_end"])
    with st.container(border=True, key="overview-drilldown"):
        st.button("Back to overview", key="overview-range-back", on_click=close_range_drilldown)
        st.subheader(markdown_label("All estimates" if band is None else band))
        st.caption(f"{period} · All airports · Report {latest_report}")
        count, amount = st.columns(2)
        count.metric("Records in this range", f"{len(rows):,}")
        amount.metric("Total reported estimate · USD", format_usd(total))
        if not rows:
            st.caption("No records with a known estimate in this range.")
        for row in rows:
            render_record_row(row, reports, "range")


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
    st.button("See the Traffic section", key="open-traffic", on_click=open_section, args=(SECTION_TRAFFIC,))


def change_text(change: int | None, percent, prior_label: str) -> str | None:
    if change is None:
        return None
    if percent is None:
        return f"{change:+,} vs {prior_label}"
    return f"{change:+,} ({percent:+.1f}%) vs {prior_label}"
