"""Explore tab: directory search, airport overview, result list and estimate ranking."""

from collections import Counter
from decimal import Decimal
from hashlib import sha256
from html import escape

import pandas as pd
import streamlit as st

from mia_capital_intelligence.app_tabs.app_common import (
    render_detail, render_estimate_distribution, render_record_summary, report_label, report_period,
)
from mia_capital_intelligence.directory_queries import (
    ESTIMATE_BANDS, SORTS, DirectoryFilters, estimate_band, format_usd, search_records,
)
from mia_capital_intelligence.estimate_insights import (
    CHART_NAMES, ESTIMATE_AXIS_TITLE, estimate_figure, largest_estimates, selected_source_ref,
)
from mia_capital_intelligence.public_registry import AIRPORTS, PublicRegistry


ALL = "all"


EXPLORE_PAGE_SIZE = 5


ESTIMATE_SORT = "Reported estimate, highest first"


def reset_explore_selection() -> None:
    st.session_state.pop("explore_record", None)
    st.session_state.pop("selected_record", None)
    st.session_state["explore_limit"] = EXPLORE_PAGE_SIZE


def sync_explore_estimates() -> None:
    reset_explore_selection()
    st.session_state["chart_airport"] = st.session_state["airport"]
    report = st.session_state["source_report"]
    if report != ALL:
        st.session_state["chart_report"] = report


def reset_explore_filters(latest_report: str, *, overview: bool) -> None:
    st.session_state["search"] = ""
    if overview:
        st.session_state["estimate_range"] = None
        st.session_state["explore_browse"] = False
        if st.session_state["source_report"] == ALL:
            st.session_state["source_report"] = latest_report
    reset_explore_selection()


def select_explore_airport(code: str) -> None:
    st.session_state["airport"] = ALL if st.session_state["airport"] == code else code
    sync_explore_estimates()


def select_explore_record(reference: str | None) -> None:
    st.session_state["explore_record"] = reference


def browse_explore_records() -> None:
    st.session_state["explore_browse"] = True
    reset_explore_selection()


def show_more_records() -> None:
    st.session_state["explore_limit"] = st.session_state.get("explore_limit", EXPLORE_PAGE_SIZE) + EXPLORE_PAGE_SIZE


def render_airport_overview(registry: PublicRegistry, matter: str, airport: str | None, coverage: str) -> None:
    population = search_records(registry, DirectoryFilters(matter_id=matter, sort=ESTIMATE_SORT))
    scoped = [row for row in population if airport is None or (row["airport_code"] or "Unknown") == airport]
    st.subheader("Airport overview")
    st.caption(f"{len(scoped)} of {len(population)} indexed source records · {coverage}")
    counts = Counter(row["airport_code"] or "Unknown" for row in population)
    top_estimates = [row for row in scoped if row["estimate_usd"] is not None][:3]
    geography, estimates = st.columns([1, 1.3], gap="medium")
    with geography, st.container(border=True, key="explore-airports"):
        st.markdown("**Indexed records by airport**")
        for code, name in (*AIRPORTS.items(), ("Unknown", "Unknown airport")):
            st.button(
                f"{name} · {counts[code]}", key=f"browse-airport-{code}", width="stretch",
                type="primary" if airport == code else "secondary", disabled=not counts[code],
                on_click=select_explore_airport, args=(code,),
            )
        noun = "source record" if len(scoped) == 1 else "source records"
        st.button(
            f"Browse {len(scoped)} {noun}", key="browse-records", on_click=browse_explore_records,
        )
    selected = st.session_state.get("explore_record")
    with estimates, st.container(border=True, key="explore-estimates"):
        st.markdown("**Largest reported estimates**")
        if not top_estimates:
            st.caption("No reported estimates for the selected airport.")
        for row in top_estimates:
            reference = row["source_ref"]
            label = CHART_NAMES.get(row["project_id"], row["project_name"])
            st.button(
                f"{escape(label)}  \n{usd_button_label(row['estimate_usd'])}", key=f"ranked-{reference}",
                width="stretch", type="primary" if selected == reference else "secondary",
                on_click=select_explore_record, args=(reference,),
            )
    if selected in {row["source_ref"] for row in top_estimates}:
        render_detail(registry, selected)


def usd_button_label(value: Decimal | None) -> str:
    # Escape the dollar sign for Streamlit's Markdown widget labels.
    return format_usd(value).replace("$", r"\$")


def render_result_table(records: list[dict], selected: str | None) -> str | None:
    frame = pd.DataFrame([
        {"Project ID": row["project_id"], "Reported project description": row["project_name"],
         "Airport": row["airport_code"] or "Unknown",
         "Reporting period": report_period(row["period_start"], row["period_end"]),
         "Reported estimate (USD)": format_usd(row["estimate_usd"]),
         "Source": row["matter_id"], "PDF page": row["pdf_page"]}
        for row in records
    ])
    st.dataframe(
        frame, hide_index=True, height=min(330, 40 + 35 * len(records)), width="stretch",
        column_config={
            "Reported project description": st.column_config.TextColumn(width="large"),
            "Reporting period": st.column_config.TextColumn(width="medium"),
        },
    )
    by_ref = {row["source_ref"]: row for row in records}
    refs = list(by_ref)
    return st.selectbox(
        "Open a source record", refs, index=refs.index(selected) if selected in by_ref else None,
        format_func=lambda ref: (
            f"{by_ref[ref]['project_id']} · {by_ref[ref]['matter_id']} · "
            f"{by_ref[ref]['project_name']}"
        ),
        key="selected_record",
    )


def render_explore_results(registry: PublicRegistry, records: list[dict], matter: str | None) -> None:
    by_ref = {row["source_ref"]: row for row in records}
    refs = list(by_ref)
    selected = st.session_state.get("explore_record")
    if st.toggle("View as table", key="explore_table"):
        selected = render_result_table(records, selected)
        select_explore_record(selected)
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
    if matter is not None and len(refs) >= 2:
        with st.expander("Compare two records from one report"):
            key = sha256(repr(refs).encode()).hexdigest()[:16]
            pair = st.multiselect(
                "Choose two source records", refs, max_selections=2, key=f"same-report-pair-{key}",
                format_func=lambda ref: f"{by_ref[ref]['project_id']} · {by_ref[ref]['project_name']}",
            )
            if len(pair) == 2:
                st.caption("Each estimate describes the scope printed for that record in the same report.")
                for column, reference in zip(st.columns(2), pair, strict=True):
                    with column:
                        render_record_summary(registry, reference, show_scope=True)


def render_directory(registry: PublicRegistry, *, latest_report: str) -> None:
    sources = {row["matter_id"]: row for row in registry.catalog if row["indexed_record_count"]}
    st.title("MIA Capital Intelligence")
    st.caption("Explore airport improvements and reported project costs.")
    with st.form("explore-search", border=False):
        search_column, search_button = st.columns([5, 1], vertical_alignment="bottom")
        with search_column:
            query = st.text_input(
                "Search projects", placeholder="Concourse D, chiller, or X078A", key="search",
            ).strip()
        with search_button:
            st.form_submit_button("Search", type="primary", on_click=reset_explore_selection, width="stretch")
    report_column, airport_column = st.columns([1, 1])
    reports = sorted(sources, key=lambda matter: sources[matter]["period_end"], reverse=True)
    with report_column:
        report_option = st.selectbox(
            "Report period", [*reports, ALL], key="source_report", on_change=sync_explore_estimates,
            format_func=lambda key: (
                "All indexed reports" if key == ALL
                else report_period(sources[key]["period_start"], sources[key]["period_end"])
            ),
        )
    with airport_column:
        airport_option = st.selectbox(
            "Airport", [ALL, *AIRPORTS, "Unknown"], key="airport", on_change=sync_explore_estimates,
            format_func=lambda code: "All airports" if code == ALL else AIRPORTS.get(code, "Unknown airport"),
        )
    matter = None if report_option == ALL else report_option
    airport = None if airport_option == ALL else airport_option
    band = st.session_state.get("estimate_range") if matter is not None else None
    source = sources.get(matter)
    coverage = report_period(source["period_start"], source["period_end"]) if source else f"{len(sources)} indexed reports"
    if query or st.session_state.get("explore_browse") or matter is None or band:
        render_directory_matches(registry, query, airport, matter, coverage, latest_report)
    else:
        render_airport_overview(registry, matter, airport, coverage)
    matters = f"Report {matter}" if matter else "Reports " + ", ".join(reports)
    st.caption(f"Miami-Dade Aviation Department · Exhibit B · {matters}")


def render_directory_matches(
    registry: PublicRegistry, query: str, airport: str | None, matter: str | None,
    coverage: str, latest_report: str,
) -> None:
    sort_column, range_column = st.columns(2)
    with sort_column:
        sort = st.selectbox(
            "Sort records", list(SORTS), index=list(SORTS).index(ESTIMATE_SORT), key="sort",
            on_change=reset_explore_selection,
        )
    band = None
    if matter is not None:
        with range_column:
            band = st.selectbox(
                "Reported estimate range", [None, *ESTIMATE_BANDS], key="estimate_range",
                format_func=lambda value: value or "All estimates", on_change=reset_explore_selection,
            )
    records = search_records(registry, DirectoryFilters(query, airport, matter, sort))
    if band is not None:
        records = [row for row in records if estimate_band(row["estimate_usd"]) == band]
    st.subheader("Search results" if query else "Source records")
    noun = "source record" if len(records) == 1 else "source records"
    st.caption(f"{len(records)} matching {noun} · {coverage}")
    st.button(
        "Clear search" if query else "Back to overview", key="explore-back",
        on_click=reset_explore_filters, args=(latest_report,), kwargs={"overview": not query},
    )
    if records:
        render_explore_results(registry, records, matter)
    else:
        st.info("No source records match these filters. Try a shorter keyword or select all airports and reports.")


def render_insights(registry: PublicRegistry, *, show_ranking: bool = False) -> None:
    sources = {row["matter_id"]: row for row in registry.catalog if row["indexed_record_count"]}
    matter = st.selectbox("Chart report period", list(reversed(sources)),
                          format_func=lambda key: report_label(sources[key]), key="chart_report")
    source = sources[matter]
    airport_filter = st.session_state.get("chart_airport", ALL)
    airport = None if airport_filter == ALL else airport_filter
    render_estimate_distribution(largest_estimates(registry, matter, airport), source, airport)
    if show_ranking:
        render_estimate_ranking(registry, matter, source)
    else:
        with st.expander("See the largest estimates"):
            render_estimate_ranking(registry, matter, source)


def render_estimate_ranking(registry: PublicRegistry, matter: str, source: dict) -> None:
    airport_col, size_col = st.columns([2, 1])
    with airport_col:
        airport_filter = st.selectbox("Chart airport", [ALL, *AIRPORTS, "Unknown"], key="chart_airport",
                                      format_func=lambda code: "All airports" if code == ALL else code)
    airport = None if airport_filter == ALL else airport_filter
    with size_col:
        limit = st.selectbox("Show largest", [5, 10, 20], index=1, key="chart_limit")
    keyword = st.text_input("Find within this chart", key="chart_search", placeholder="Project ID or keyword")
    ranking = largest_estimates(registry, matter, airport, keyword, limit)
    st.caption(
        f"Showing the {len(ranking.rows)} largest of {ranking.matching_count} records. "
        f"{ranking.missing_count} records have no reported estimate."
    )
    if not ranking.rows:
        st.info("No known cost estimates match these chart filters. Try a different airport or keyword.")
        return
    # A filter-specific chart key prevents a previous chart's event selecting a new population.
    token = sha256(repr((matter, airport, keyword, limit)).encode()).hexdigest()[:16]
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
        reference = st.selectbox(
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
    st.html("""
        <style>
        :is(.st-key-explore-airports, .st-key-explore-estimates, .st-key-explore-record-list)
          button[data-testid^="stBaseButton"] { justify-content:flex-start; text-align:left; }
        .st-key-explore-record-list button[data-testid^="stBaseButton"] { padding:.65rem .85rem; }
        :is(.st-key-explore-airports, .st-key-explore-estimates, .st-key-explore-record-list)
          button[data-testid^="stBaseButton"] p { overflow-wrap:anywhere; }
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
    """)
    render_directory(registry, latest_report=latest_report)
    if st.session_state.get("airport", ALL) != ALL:
        st.subheader("Estimate ranges and interactive ranking")
        render_insights(registry, show_ranking=True)
    else:
        with st.expander("Estimate ranges and interactive ranking"):
            render_insights(registry)
