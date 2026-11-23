"""Projects section: opened by a service-area tile or a search, with record lists, detail and the estimate ranking."""

from hashlib import sha256
from html import escape

import pandas as pd
import streamlit as st

from mia_capital_intelligence.app_tabs.app_common import (
    SECTIONS, open_report, open_section, render_detail, render_record_summary, report_label, report_period,
)
from mia_capital_intelligence.directory_queries import (
    ESTIMATE_BANDS, SORTS, DirectoryFilters, estimate_band, format_usd, search_records,
)
from mia_capital_intelligence.estimate_insights import (
    ESTIMATE_AXIS_TITLE, estimate_figure, largest_estimates, selected_source_ref,
)
from mia_capital_intelligence.operations_updates import OPERATING_AREAS, OPERATIONS_MATTER, operations_updates
from mia_capital_intelligence.public_registry import AIRPORTS, PublicRegistry

ALL = "all"
ALL_RANGES = "All estimates"
EXPLORE_PAGE_SIZE = 5
ESTIMATE_SORT = "Reported estimate, highest first"
CHART_LIMITS = (5, 10, 20)
COMPARE_LIMIT = 20

PROJECTS_CSS = """
    <style>
    .st-key-explore-record-list button[data-testid^="stBaseButton"],
    .st-key-explore-cards button[data-testid^="stBaseButton"] { justify-content:flex-start; text-align:left; }
    .st-key-explore-record-list button[data-testid^="stBaseButton"] { padding:.65rem .85rem; }
    :is(.st-key-explore-record-list, .st-key-explore-cards) button[data-testid^="stBaseButton"] p {
      overflow-wrap:anywhere; }
    .st-key-estimate-ranking-layout { container: estimate-ranking / inline-size; }
    @container estimate-ranking (max-width: 50rem) {
      [data-testid="stHorizontalBlock"]:has(.st-key-ranked-record) { flex-direction:column; }
      [data-testid="stHorizontalBlock"]:has(.st-key-ranked-record) > [data-testid="stColumn"] {
        flex:none; width:100%; min-width:0;
      }
    }
    .st-key-ranked-record :is([data-testid="stMetricLabel"], [data-testid="stMetricValue"],
      [data-testid="stMetricLabel"] p, [data-testid="stMetricValue"] > div) {
      white-space:normal; overflow:visible; overflow-wrap:anywhere; text-overflow:clip;
    }
    .st-key-ranked-record .mia-ranked-brief { margin:0; overflow-wrap:anywhere; }
    .st-key-ranked-evidence-links a { color:#337AB7; padding:.25rem .5rem; min-height:2.75rem; }
    .st-key-ranked-evidence-links a p { color:inherit; font-size:.875rem; text-decoration:underline; }
    .st-key-ranked-evidence-links a:is(:hover,:focus-visible) { color:#012851; }
    </style>
"""


def sources_by_matter(registry: PublicRegistry) -> dict[str, dict]:
    return {row["matter_id"]: row for row in registry.catalog if row["indexed_record_count"]}


def latest_matter(sources: dict[str, dict]) -> str:
    return max(sources, key=lambda matter: sources[matter]["period_end"])


def reset_explore_selection() -> None:
    st.session_state.pop("explore_record", None)
    st.session_state["explore_limit"] = EXPLORE_PAGE_SIZE


def select_explore_record(reference: str | None) -> None:
    st.session_state["explore_record"] = reference


def show_more_records() -> None:
    st.session_state["explore_limit"] = st.session_state.get("explore_limit", EXPLORE_PAGE_SIZE) + EXPLORE_PAGE_SIZE


def browse_records() -> None:
    st.session_state["explore_browse"] = True
    reset_explore_selection()


def clear_projects() -> None:
    st.session_state.update(search="", area=None, explore_browse=False)
    reset_explore_selection()


def submit_search() -> None:
    """A search replaces any service-area drill-down."""
    st.session_state.update(area=None, explore_browse=False)
    reset_explore_selection()


def select_service_area() -> None:
    st.session_state["search"] = ""
    reset_explore_selection()


def open_service_area(area: str) -> None:
    """Callback for an overview tile: go straight to the projects for that service area."""
    st.session_state.update(area=area, search="", explore_browse=False)
    reset_explore_selection()
    open_section(SECTIONS[1])


def open_projects_range(matter_id: str, band: str | None) -> None:
    """Callback for the Overview range list: open the same report and estimate range in Projects."""
    st.session_state.update(
        source_report=matter_id, estimate_range=ALL_RANGES if band is None else band,
        area=None, search="", explore_browse=True,
    )
    reset_explore_selection()
    open_section(SECTIONS[1])


def markdown_label(text: str) -> str:
    """Escape dollar signs so Streamlit's Markdown widget labels do not read '$...$' pairs as math."""
    return text.replace("$", r"\$")


def open_projects_search(query: str) -> None:
    """Callback for the overview search: show the matching projects and reports in the Projects section."""
    st.session_state.update(search=query.strip(), area=None, explore_browse=False)
    reset_explore_selection()
    open_section(SECTIONS[1])


def matches_report(source: dict, query: str) -> bool:
    text = f"{report_label(source)} {source['title']}".lower()
    return all(word in text for word in query.lower().split())


def render_service_area(registry: PublicRegistry, area: str) -> None:
    updates = [update for update in operations_updates(registry) if update.area == area]
    source = next(row for row in registry.catalog if row["matter_id"] == OPERATIONS_MATTER)
    st.subheader(area)
    noun = "project update" if len(updates) == 1 else "project updates"
    st.caption(f"{len(updates)} {noun} from the county's quarterly report")
    selected = st.session_state.get("explore_record")
    with st.container(key="explore-cards"):
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
                    on_click=select_explore_record, args=(reference,),
                )
    if selected in {update.source_ref for update in updates}:
        render_detail(registry, selected)


def usd_button_label(value) -> str:
    return markdown_label(format_usd(value))


def render_report_matches(sources: dict[str, dict], query: str) -> None:
    matches = [source for source in sources.values() if matches_report(source, query)]
    if not matches:
        return
    st.markdown("**Reports matching this search**")
    for source in matches:
        st.button(
            f"{report_label(source)} · {source['title']}", key=f"report-{source['matter_id']}",
            width="stretch", on_click=open_report, args=(source["matter_id"],),
        )


def render_result_table(records: list[dict], refs: tuple[str, ...]) -> None:
    frame = pd.DataFrame([
        {"Project ID": row["project_id"], "Reported project description": row["project_name"],
         "Airport": row["airport_code"] or "Unknown",
         "Reporting period": report_period(row["period_start"], row["period_end"]),
         "Reported estimate (USD)": format_usd(row["estimate_usd"]),
         "Source": row["matter_id"], "PDF page": row["pdf_page"]}
        for row in records
    ])
    token = sha256(repr(refs).encode()).hexdigest()[:16]
    event = st.dataframe(
        frame, hide_index=True, height=min(330, 40 + 35 * len(records)), width="stretch",
        on_select="rerun", selection_mode="single-row", key=f"record-table-{token}",
        column_config={
            "Reported project description": st.column_config.TextColumn(width="large"),
            "Reporting period": st.column_config.TextColumn(width="medium"),
        },
    )
    rows = event.selection.rows
    if rows:
        select_explore_record(refs[rows[0]])


def render_explore_results(registry: PublicRegistry, records: list[dict], matter: str | None) -> None:
    by_ref = {row["source_ref"]: row for row in records}
    refs = tuple(by_ref)
    selected = st.session_state.get("explore_record")
    if st.toggle("View as table", key="explore_table"):
        render_result_table(records, refs)
        selected = st.session_state.get("explore_record")
    else:
        limit = st.session_state.get("explore_limit", EXPLORE_PAGE_SIZE)
        with st.container(key="explore-record-list"):
            for row in records[:limit]:
                reference = row["source_ref"]
                period = report_period(row["period_start"], row["period_end"])
                label = (
                    f"**{escape(row['project_name'])}**  \n"
                    f"{row['project_id']} · {row['airport_name']} · {period} · "
                    f"**{usd_button_label(row['estimate_usd'])}**"
                )
                st.button(
                    label, key=f"record-{reference}", width="stretch",
                    type="primary" if selected == reference else "secondary",
                    on_click=select_explore_record, args=(reference,),
                )
        if len(records) > limit:
            st.button("Show more results", key="explore-more", on_click=show_more_records)
    if selected in by_ref:
        render_detail(registry, selected)
    if matter is not None and 2 <= len(refs) <= COMPARE_LIMIT:
        with st.expander("Compare two records from one report"):
            key = sha256(repr(refs).encode()).hexdigest()[:16]
            pair = list(st.pills(
                "Choose two source records", refs, selection_mode="multi", key=f"same-report-pair-{key}",
                format_func=lambda ref: f"{by_ref[ref]['project_id']} · {by_ref[ref]['project_name']}",
            ) or [])[-2:]
            if len(pair) < 2:
                st.caption("Select two records to compare them.")
            else:
                st.caption("Each estimate describes the scope printed for that record in the same report.")
                for column, reference in zip(st.columns(2), pair, strict=True):
                    with column:
                        render_record_summary(registry, reference, show_scope=True)


def render_record_list(registry: PublicRegistry, sources: dict[str, dict], query: str, latest_report: str) -> None:
    reports = sorted(sources, key=lambda matter: sources[matter]["period_end"], reverse=True)
    st.session_state.setdefault("source_report", latest_report)
    matter = st.radio(
        "Report period", [*reports, ALL], key="source_report", horizontal=True, on_change=reset_explore_selection,
        format_func=lambda key: (
            "All indexed reports" if key == ALL
            else report_period(sources[key]["period_start"], sources[key]["period_end"])
        ),
    )
    matter = None if matter == ALL else matter
    st.session_state.setdefault("airport", ALL)
    airport_choice = st.radio(
        "Airport", [ALL, *AIRPORTS, "Unknown"], key="airport", horizontal=True, on_change=reset_explore_selection,
        format_func=lambda code: "All airports" if code == ALL else AIRPORTS.get(code, "Unknown airport"),
    )
    airport = None if airport_choice == ALL else airport_choice
    band = None
    if matter is not None:
        st.session_state.setdefault("estimate_range", ALL_RANGES)
        band_choice = st.radio(
            "Reported estimate range", [ALL_RANGES, *ESTIMATE_BANDS], key="estimate_range", horizontal=True,
            on_change=reset_explore_selection, format_func=markdown_label,
        )
        band = None if band_choice == ALL_RANGES else band_choice
    st.session_state.setdefault("sort", ESTIMATE_SORT)
    sort = st.radio("Sort records", list(SORTS), key="sort", horizontal=True, on_change=reset_explore_selection)
    records = search_records(registry, DirectoryFilters(query, airport, matter, sort))
    if band is not None:
        records = [row for row in records if estimate_band(row["estimate_usd"]) == band]
    coverage = (report_period(sources[matter]["period_start"], sources[matter]["period_end"])
                if matter else f"{len(sources)} indexed reports")
    st.subheader("Search results" if query else "Source records")
    noun = "source record" if len(records) == 1 else "source records"
    st.caption(f"{len(records)} matching {noun} · {coverage}")
    if query:
        render_report_matches(sources, query)
    st.button("Clear search" if query else "Hide source records", key="explore-clear", on_click=clear_projects)
    if records:
        render_explore_results(registry, records, matter)
    else:
        st.info("No source records match these filters. Try a shorter keyword or select all airports and reports.")


def render_insights(registry: PublicRegistry, sources: dict[str, dict]) -> None:
    matters = sorted(sources, key=lambda matter: sources[matter]["period_end"], reverse=True)
    st.session_state.setdefault("chart_report", latest_matter(sources))
    matter = st.radio("Chart report period", matters, key="chart_report", horizontal=True,
                      format_func=lambda key: report_label(sources[key]))
    st.session_state.setdefault("chart_airport", ALL)
    airport_choice = st.radio(
        "Chart airport", [ALL, *AIRPORTS, "Unknown"], key="chart_airport", horizontal=True,
        format_func=lambda code: "All airports" if code == ALL else code,
    )
    airport = None if airport_choice == ALL else airport_choice
    limit = st.radio("Show largest", list(CHART_LIMITS), index=CHART_LIMITS.index(10), key="chart_limit",
                     horizontal=True, format_func=str)
    ranking = largest_estimates(registry, matter, airport, "", limit)
    st.caption(
        f"Showing the {len(ranking.rows)} largest of {ranking.matching_count} records. "
        f"{ranking.missing_count} records have no reported estimate."
    )
    if not ranking.rows:
        st.info("No known cost estimates match these chart filters. Try a different airport or report.")
        return
    source = sources[matter]
    # A filter-specific chart key prevents a previous chart's event selecting a new population.
    token = sha256(repr((matter, airport, limit)).encode()).hexdigest()[:16]
    with st.container(key="estimate-ranking-layout"):
        chart, evidence = st.columns([3, 2], gap="medium")
    with chart:
        event = st.plotly_chart(
            estimate_figure(ranking), width="stretch", key=f"estimates-{token}",
            on_select="rerun", selection_mode="points", config={"displayModeBar": False, "scrollZoom": False},
        )
        # The axis title sits below the plot so it stays whole on narrow screens.
        st.caption(ESTIMATE_AXIS_TITLE)
        selected = selected_source_ref(event, ranking)
        detail_key, event_key = f"chart-detail-{token}", f"chart-event-{token}"
        if selected and st.session_state.get(event_key) != selected:
            st.session_state[detail_key] = selected
        st.session_state[event_key] = selected
        by_ref = {row["source_ref"]: row for row in ranking.rows}
        st.session_state.setdefault(detail_key, next(iter(by_ref)))
        reference = st.radio(
            "Explore a chart record", list(by_ref), key=detail_key,
            format_func=lambda ref: f"{by_ref[ref]['project_id']} · {by_ref[ref]['project_name']}",
        )
    with evidence:
        render_record_summary(registry, reference)
    with st.popover("Exact values and source pages"):
        st.dataframe(pd.DataFrame([
            {"Project ID": row["project_id"], "Description": row["project_name"],
             "Estimated cost (USD)": format_usd(row["estimate_usd"]),
             "Official evidence": f"{source['url']}#page={row['pdf_page']}"}
            for row in ranking.rows
        ]), hide_index=True, width="stretch",
            column_config={"Official evidence": st.column_config.LinkColumn("Official evidence")})


def render_explore_tab(registry: PublicRegistry, latest_report: str) -> None:
    st.html(PROJECTS_CSS)
    sources = sources_by_matter(registry)
    st.subheader("Projects")
    st.caption("Search for a project or report, choose a service area, or show all source records.")
    with st.form("explore-search", border=False):
        search_column, search_button = st.columns([5, 1], vertical_alignment="bottom")
        with search_column:
            query = st.text_input(
                "Search projects and reports", placeholder="Concourse D, chiller, X078A, or 261402", key="search",
            ).strip()
        with search_button:
            st.form_submit_button("Search", type="primary", on_click=submit_search, width="stretch")
    area = st.radio("Service area", OPERATING_AREAS, index=None, key="area", horizontal=True,
                    on_change=select_service_area)
    if area is not None:
        render_service_area(registry, area)
    elif query or st.session_state.get("explore_browse"):
        render_record_list(registry, sources, query, latest_report)
    else:
        st.info("Search for a project or report, choose a service area, or show all source records.")
        st.button("Show all source records", key="browse-records", on_click=browse_records)
    with st.expander("Estimate ranges and interactive ranking"):
        render_insights(registry, sources)
    matters = ", ".join(sorted(sources, reverse=True))
    st.caption(f"Miami-Dade Aviation Department · Exhibit B · Reports {matters}")
