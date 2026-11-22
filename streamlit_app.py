"""Read-only public directory for controlled MDAD source observations."""

import os
import sys
from collections import Counter
from datetime import date
from decimal import Decimal
from hashlib import sha256
from html import escape
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mia_capital_intelligence.directory_queries import (  # noqa: E402
    ESTIMATE_BANDS, DirectoryFilters, SORTS, estimate_band, format_usd, search_records, source_detail,
)
from mia_capital_intelligence.public_registry import AIRPORTS, PublicRegistry, load_registry  # noqa: E402
from mia_capital_intelligence.estimate_insights import (  # noqa: E402
    CHART_NAMES, EstimateRanking, apply_chart_theme, estimate_figure, largest_estimates,
    selected_source_ref,
)
from mia_capital_intelligence.contract_spending import FinancialView, financial_view  # noqa: E402
from mia_capital_intelligence.operations_updates import (  # noqa: E402
    OPERATING_AREAS, OPERATIONS_MATTER, operations_updates,
)

CASE_REFS = (
    "260526:eaf845f4fb746a69940f38fe4655d27b56ab42effdbf9cfdd1dbc746a0fba878:B:11:63",
    "261402:84751b451da8b7d5e06cad6b1c24c870e563de5669c5f07325033c446bbaeb2a:B:12:65",
    "260526:eaf845f4fb746a69940f38fe4655d27b56ab42effdbf9cfdd1dbc746a0fba878:B:11:64",
)
EXPLORE_PAGE_SIZE = 5
ESTIMATE_SORT = "Reported estimate, highest first"
ALL = "all"

st.set_page_config(page_title="MIA Capital Intelligence", page_icon="✈", layout="wide")
INDEPENDENT_NOTICE = (
    "An independent data project. Not affiliated with or endorsed by Miami International Airport "
    "or Miami-Dade County. Records are attributed to their publishing organizations."
)
st.html("""
    <style>
    @import url("https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap");
    .stApp, .stApp p, .stApp label, .stApp li, .stApp td, .stApp th, .stApp input, .stApp textarea,
    .stApp [data-testid="stMarkdownContainer"], .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
      font-family: Roboto, "Helvetica Neue", sans-serif;
    }
    .stApp h1, .stApp h2, .stApp h3 { color:#012851; font-weight:700; }
    </style>
""")


@st.cache_resource(show_spinner=False)
def published_registry() -> PublicRegistry:
    """Cache immutable published inputs, with a fresh in-memory SQL query per search."""
    return load_registry(ROOT)


def report_label(source: dict) -> str:
    return f"{source['period_start']} to {source['period_end']} · {source['matter_id']}"


def report_period(start: str, end: str) -> str:
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first.year == last.year:
        return f"{first:%b}–{last:%b %Y}"
    return f"{first:%b %Y}–{last:%b %Y}"


def profile_permalink(source_ref: str) -> str:
    return "?" + urlencode({"record": source_ref})


def render_project_brief(detail: dict, *, expanded: bool, include_brief: bool = True) -> None:
    delivery = detail["delivery"]
    has_brief = include_brief and detail["project_brief"] != detail["project_name"]
    if not has_brief and not delivery:
        return
    title = "Project brief and delivery team" if delivery and (delivery.lead or delivery.award) else "Project brief"
    if not include_brief:
        title = "Delivery team"
    with st.expander(title, expanded=expanded):
        if has_brief:
            st.html(f'<p style="margin:0; overflow-wrap:anywhere">{escape(detail["project_brief"])}</p>')
        st.markdown(f"**Reporting agency** · {detail['reporting_agency']}")
        if delivery is None:
            return
        if lead := delivery.lead:
            st.markdown(f"**Project lead** · {lead.name}")
            st.caption(
                f"MDAD project manager named in the {delivery.adopted_on:%B %Y} "
                f"[award memo]({delivery.packet_url}#page={lead.memo_page})."
            )
        if award := delivery.award:
            st.markdown(f"**Awarded contractor** · {award.company}")
            st.caption(
                f"{award.scope} · {award.contract_id} · "
                f"[Board award]({delivery.board_url}) · {delivery.adopted_on:%B %d, %Y}"
            )


def render_record_summary(registry: PublicRegistry, reference: str, *, show_scope: bool = False) -> None:
    detail = source_detail(registry, reference)
    source = detail["source"]
    if not show_scope:
        with st.container(border=True, key="ranked-record"):
            st.subheader(detail["project_name"])
            period = report_period(source["period_start"], source["period_end"])
            st.caption(f"{detail['project_id']} · {detail['airport_name']} · {period}")
            st.metric("Reported total cost estimate · USD", format_usd(detail["estimate_usd"]))
            if detail["project_brief"] != detail["project_name"]:
                st.markdown("**Project brief**")
                st.html(f'<p class="mia-ranked-brief">{escape(detail["project_brief"])}</p>')
            with st.container(horizontal=True, gap=None, key="ranked-evidence-links"):
                st.link_button(f"Open official PDF · page {detail['pdf_page']}", detail["source_page_url"], type="tertiary")
                st.link_button("Open profile permalink", profile_permalink(reference), type="tertiary")
            render_project_brief(detail, expanded=False, include_brief=False)
        return
    with st.container(border=True):
        st.caption(f"{detail['project_id']} · {detail['airport_name']} · {report_label(source)}")
        st.subheader(detail["project_name"])
        st.metric("Reported total cost estimate · USD", format_usd(detail["estimate_usd"]))
        st.write("**Scope as described in the report**")
        st.text(detail["description_raw"])
        st.link_button(f"Open official PDF · page {detail['pdf_page']}", detail["source_page_url"], type="primary")
        st.link_button("Open profile permalink", profile_permalink(reference))


def render_estimate_distribution(
    ranking: EstimateRanking, source: dict, airport: str | None, *, show_context: bool = True,
) -> None:
    known_count = ranking.matching_count - ranking.missing_count
    if not known_count:
        st.info("No indexed records with a known estimate match the selected report and airport.")
        return
    if show_context:
        st.markdown(f"**{ranking.band_counts[0]} of {ranking.matching_count} matching records** show estimates under $10 million.")
    bars = []
    for band, count in zip(ESTIMATE_BANDS, ranking.band_counts, strict=True):
        filters = {"report": ranking.matter_id, "range": band}
        if airport is not None:
            filters["airport"] = airport
        route = "?" + urlencode(filters)
        label = f"{escape(band)} <strong>{count}</strong>"
        track = f'<span class="mia-band-track" aria-hidden="true"><i style="width:{count / known_count:.2%}"></i></span>'
        content = f'<span class="mia-band-label">{label}</span>{track}'
        if count:
            noun = "record" if count == 1 else "records"
            bars.append(f'<a href="{escape(route)}" target="_blank" rel="noopener" '
                        f'aria-label="{escape(band)} · {count} {noun}">{content}</a>')
        else:
            bars.append(f'<div class="mia-band-zero">{content}</div>')
    st.html('''
        <style>
        .mia-estimate-bands { display:grid; gap:.35rem; max-width:52rem }
        .mia-estimate-bands a, .mia-band-zero { display:block; padding:.4rem .55rem;
          color:#333333; text-decoration:none; border:1px solid transparent; border-radius:.35rem }
        .mia-estimate-bands a:hover { background:#F4F7FA; text-decoration:underline }
        .mia-estimate-bands a:focus-visible { outline:2px solid #337AB7 }
        .mia-band-label { display:flex; justify-content:space-between; gap:1rem }
        .mia-band-label strong { font-variant-numeric:tabular-nums; color:#012851 }
        .mia-band-track { display:block; margin-top:.2rem; height:.45rem; background:#E4EAF0; border-radius:2px }
        .mia-band-track i { display:block; height:100%; background:#007BB6; border-radius:2px }
        </style>
        <div class="mia-estimate-bands" role="group" aria-label="Source record counts by estimate range in USD">'''
        + "".join(bars) + "</div>")
    if show_context:
        st.caption(
            f"Miami-Dade County · Matter {source['matter_id']} · {known_count} records with estimates · "
            f"{ranking.missing_count} without. Select a range to see the records behind it."
        )


def render_dashboard(registry: PublicRegistry, reports: dict, latest_report: str) -> None:
    st.header("Airport Operations")
    st.write("See how MIA is upgrading the services passengers and aircraft rely on.")
    source = reports.get(OPERATIONS_MATTER)
    if source:
        period = report_period(source["period_start"], source["period_end"])
        memo_date = date.fromisoformat(source["memo_date"])
        st.caption(f"Miami International Airport · {period} report · Memo dated {memo_date:%b %d, %Y} · "
                   f"[Official report]({source['url']})")
        area = st.radio("Choose an area", ("All areas", *OPERATING_AREAS),
                        horizontal=True, key="dashboard_area")
        st.subheader("Operations updates")
        matches = [update for update in operations_updates(registry)
                   if area == "All areas" or update.area == area]
        if not matches:
            st.info("No operations updates in this view.")
            st.link_button("Explore project records", "?", type="tertiary")
        for update in matches:
            with st.container(border=True):
                st.caption(f"{update.area} · {update.project_id}")
                st.markdown(f"### {update.title}")
                st.write(update.description)
                st.markdown(
                    f"[View project]({profile_permalink(update.source_ref)}) · "
                    f"[Read report update]({source['url']}#page={update.memo_page})"
                )
    else:
        st.info("No operations updates in this view.")
        st.link_button("Explore project records", "?", type="tertiary")

    with st.expander("Reported Estimates by Size"):
        choices = sorted(reports, key=lambda matter: reports[matter]["period_end"], reverse=True)
        matter = st.selectbox("Estimate report period", choices, index=choices.index(latest_report),
                              format_func=lambda key: report_period(reports[key]["period_start"],
                                                                  reports[key]["period_end"]),
                              key="dashboard_estimate_report")
        estimate_source = reports[matter]
        ranking = largest_estimates(registry, matter, limit=1)
        estimate_period = report_period(estimate_source["period_start"], estimate_source["period_end"])
        st.caption(f"{estimate_period} · All airports · {ranking.snapshot_count} report entries · "
                   f"[Official report]({estimate_source['url']})")
        if ranking.missing_count:
            st.caption(f"{ranking.missing_count} without a reported estimate")
        render_estimate_distribution(ranking, estimate_source, None, show_context=False)


def render_detail(registry: PublicRegistry, source_ref: str) -> None:
    detail = source_detail(registry, source_ref)
    source = detail["source"]
    with st.container(border=True):
        st.subheader(detail["project_name"])
        period = report_period(source["period_start"], source["period_end"])
        st.caption(f"{detail['project_id']} · {detail['airport_name']} · {period}")
        st.metric("Reported total cost estimate · USD", format_usd(detail["estimate_usd"]))
        st.link_button(
            f"Open official PDF · page {detail['pdf_page']}",
            detail["source_page_url"], type="primary",
        )
        st.link_button("Open profile permalink", profile_permalink(detail["source_ref"]))
        render_project_brief(detail, expanded=True)
        with st.expander("Report and source details"):
            st.write(source["title"])
            st.caption(f"{detail['reporting_agency']} · Matter {source['matter_id']} · Exhibit B")
            st.caption(f"Report coverage · {source['period_start']} to {source['period_end']}")
            st.write(f"Memo · {source['memo_date']} · Board acceptance · {source['accepted_date']}")
            st.write(f"PDF page {detail['pdf_page']} · printed {detail['printed_page']} · data row {detail['row_ordinal']}")
            st.caption("The reported amount is a planning estimate.")
            st.write("**Original project description**")
            st.text(detail["description_raw"])
            if detail["airport_code"] is None:
                st.caption("Airport: unknown. The description does not identify a single airport.")
            st.write("**Original estimate header and cell**")
            st.text(detail["estimate_header"] + "\n" + detail["estimate_raw"])
        if detail["candidate_source_refs"]:
            with st.expander("Same ID in another report"):
                st.caption("Whether these entries describe the same project scope is unknown.")
                for related_ref in detail["candidate_source_refs"]:
                    related = source_detail(registry, related_ref)
                    st.write(
                        f"**{related['project_id']} · {related['source']['matter_id']}**  "
                        f"{related['project_name']}"
                    )
                    st.write(
                        f"{related['source']['period_start']} to {related['source']['period_end']} · "
                        f"Source-reported estimate {format_usd(related['estimate_usd'])}"
                    )
                    st.link_button(
                        f"Open related official source · page {related['pdf_page']}",
                        related["source_page_url"],
                    )
                    st.link_button(
                        "Explore this related source record",
                        profile_permalink(related_ref),
                    )


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
        f"Showing {len(ranking.rows)} largest of {ranking.matching_count} matching source records "
        f"in {ranking.snapshot_count} indexed rows. {ranking.missing_count} matching records have unknown estimates."
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
                f"{escape(label)} · {usd_button_label(row['estimate_usd'])}", key=f"ranked-{reference}",
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
         "Reporting period": f"{row['period_start']} to {row['period_end']}",
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
    st.caption(INDEPENDENT_NOTICE)
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
    matters = f"Matter {matter}" if matter else "Matters " + ", ".join(reports)
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
    st.subheader("Search results" if query else "Project records")
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


def render_coverage(registry: PublicRegistry) -> None:
    st.subheader("Sources & data coverage")
    st.caption(INDEPENDENT_NOTICE + " Underlying records are published by Miami-Dade County.")
    st.markdown("[Data update history](https://github.com/jiajinz/mia-capital-intelligence/blob/main/docs/DATA_UPDATES.md)")
    if set(CASE_REFS).issubset(row.source_ref for row in registry.records):
        with st.expander("Case study · Concourse D west extension"):
            st.write(
                "Both reports list T180B with the same building expansion and apron description. "
                "The earlier report separately lists T180D for D60 apron and utilities."
            )
            for column, reference in zip(st.columns(2), CASE_REFS[:2], strict=True):
                with column:
                    render_record_summary(registry, reference, show_scope=True)
            earlier_apron = source_detail(registry, CASE_REFS[2])
            st.link_button("Open the earlier T180D source record", profile_permalink(earlier_apron["source_ref"]))
    st.write(
        f"The directory contains {len(registry.records)} source records from Exhibit B of two quarterly reports. "
        "Each record represents one entry in one report."
    )
    st.dataframe(pd.DataFrame([
        {"Matter": row["matter_id"], "Report coverage": f"{row['period_start']} to {row['period_end']}",
         "Project records": row["indexed_record_count"]}
        for row in registry.catalog
    ]), hide_index=True, width="stretch")
    sources = {row["matter_id"]: row for row in registry.catalog}
    matter = st.selectbox(
        "Inspect a source document", list(sources),
        format_func=lambda key: f"{key} · {sources[key]['title']}",
        key="coverage_source",
    )
    source = sources[matter]
    with st.container(border=True):
        st.subheader(source["title"])
        st.caption(source["publishing_organization"])
        st.write(f"**Reporting period**  {source['period_start']} to {source['period_end']}")
        st.write(f"**Memo date**  {source['memo_date']} · **Board acceptance**  {source['accepted_date']}")
        if source["indexed_pdf_pages"]:
            pages = ", ".join(map(str, source["indexed_pdf_pages"]))
            st.write(f"**Project records**  {source['indexed_record_count']} entries from Exhibit B, PDF pages {pages}.")
        if matter == OPERATIONS_MATTER and (updates := operations_updates(registry)):
            st.write(f"**Dashboard**  {len(updates)} project updates from the report narrative, PDF pages 5–7.")
        if matter == "261400":
            st.write("**Contract spending**  Exhibit B, PDF page 30, and the Summary of Changes, pages 21–22.")
        st.link_button("Open official source document", source["url"], type="primary")
        st.link_button("Open county legislative record", source["matter_url"])


def configured_financial_review() -> str | None:
    """Use the local record only when no Streamlit review is configured."""
    try:
        review = st.secrets.get("financial_review")
    except StreamlitSecretNotFoundError as error:
        return None if error.__cause__ is None else ""
    except OSError:
        return ""
    if review is None:
        return None
    try:
        document = review["attestation_json"]
    except (KeyError, TypeError):
        return ""
    return document if isinstance(document, str) else ""


def render_contract_spending(view: FinancialView) -> None:
    st.subheader("Contract spending history")
    if not view.rows:
        st.info("Contract spending data is currently unavailable.")
        return
    if view.local_review and view.status != "approved":
        st.warning("Local review preview.")
    st.caption("July–September 2026 · Four contracts · Three monthly Aviation Capital Program reports")
    contracts = sorted({row.contract_id for row in view.rows})
    contract = st.selectbox("Contract", contracts, index=contracts.index("A19-MDAD-02"), key="spending_contract")
    rows = [row for row in view.rows if row.contract_id == contract]
    figure = go.Figure(go.Bar(
        x=[row.month_label for row in rows], y=[float(row.monthly_usd) for row in rows],
        text=[f"${row.monthly_usd:,.2f}" for row in rows], textposition="outside", cliponaxis=False,
        customdata=[[f"${row.monthly_usd:,.2f}", "Summary confirms zero" if row.monthly_dash_corroborated
                     else "Financial table amount"] for row in rows],
        hovertemplate="%{x}<br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
        marker_color="#007BB6",
    ))
    figure.update_layout(
        title="Reported monthly expenditures", height=320, margin=dict(l=12, r=18, t=55, b=32),
        xaxis_title="Reported month", yaxis_title="Expenditures (USD)",
        yaxis_tickprefix="$", yaxis_rangemode="tozero", showlegend=False,
    )
    apply_chart_theme(figure)
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False, "scrollZoom": False})
    with st.expander("How the cumulative amount adds up"):
        first, last = rows[0], rows[-1]
        months = sum(row.monthly_usd for row in rows)
        st.markdown(
            rf"**\${first.prior_usd:,.2f}** reported before July + **\${months:,.2f}** reported in July–September "
            rf"= **\${last.cumulative_usd:,.2f}** reported through September."
        )
        st.caption("USD · These amounts follow the reporting months. The accounting cutoff is unknown.")
        st.link_button(f"Opening amount · July financial table, p. {first.financial_page}", first.financial_url)
        for row in rows:
            st.link_button(f"{row.month_label} · financial table, p. {row.financial_page}", row.financial_url)
    st.dataframe(pd.DataFrame([
        {"Reported month": row.month_label, "Monthly expenditures": f"${row.monthly_usd:,.2f}",
         "Cumulative expenditures": f"${row.cumulative_usd:,.2f}",
         "Financial PDF": row.financial_url, "Summary PDF": row.summary_url,
         "Monthly cell evidence": "Dash corroborated by summary zero" if row.monthly_dash_corroborated
         else "Numeric amount in financial table"}
        for row in rows
    ]), hide_index=True, width="stretch", column_config={
        "Financial PDF": st.column_config.LinkColumn(display_text="Open financial page"),
        "Summary PDF": st.column_config.LinkColumn(display_text="Open summary page"),
    })
    with st.expander("Original evidence and coverage"):
        st.write("Publisher: Miami-Dade County. The sample contains four contract rows per reported month.")
        st.write("Contracts in this slice: " + ", ".join(contracts))
        st.caption("Spending is reported per contract. The accounting cutoff and accounting basis are unknown.")
        for row in rows:
            st.write(f"**{row.month_label}** · {row.raw_contract} · {row.printed_page} row {row.row_ordinal}")
            st.link_button(f"Open {row.month_label} financial PDF · page {row.financial_page}", row.financial_url)
            st.link_button(f"Open {row.month_label} summary · page {row.summary_page} row {row.summary_row_ordinal}", row.summary_url)
            if row.monthly_dash_corroborated:
                st.caption("The summary explicitly reports $0.00 for the financial table's monthly dash.")
        if contract == "E20-MDAD-03":
            st.caption("The same-issue summaries use E20-MDAD-03. The financial tables print E20-MDAD--03.")
        if contract == "A19-MDAD-01":
            st.caption("Airport: unknown. The financial table and monthly summary give different locations.")


try:
    registry = published_registry()
except (ValueError, OSError, KeyError):
    st.title("MIA Capital Intelligence")
    st.error("The published data could not be validated. Project records are unavailable until the data is repaired.")
    st.stop()

if "record" in st.query_params:
    st.title("MIA Capital Intelligence")
    requested = st.query_params.get_all("record")
    st.link_button("Browse project records", "?")
    if len(requested) == 1 and any(row.source_ref == requested[0] for row in registry.records):
        render_detail(registry, requested[0])
    else:
        st.warning("This record link is outside the current registry version or is invalid. Open the directory to choose an available record.")
    st.stop()

reports = {source["matter_id"]: source for source in registry.catalog if source["indexed_record_count"]}
latest_report = max(reports, key=lambda matter: reports[matter]["period_end"])
report_route = st.query_params.get_all("report")
range_route = st.query_params.get_all("range")
airport_route = st.query_params.get_all("airport")
if not st.session_state.get("explore_initialized"):
    if (len(report_route) == len(range_route) == 1
            and report_route[0] in reports and range_route[0] in ESTIMATE_BANDS):
        st.session_state.update(source_report=report_route[0], chart_report=report_route[0],
                                estimate_range=range_route[0], explore_browse=True)
        if len(airport_route) == 1 and airport_route[0] in (*AIRPORTS, "Unknown"):
            st.session_state.update(airport=airport_route[0], chart_airport=airport_route[0])
    st.session_state["explore_initialized"] = True

explore_tab, dashboard_tab, coverage_tab, spending_tab = st.tabs([
    "Explore", "Dashboard", "Sources & methodology", "Contract spending history",
], default="Explore")
with explore_tab:
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
with dashboard_tab:
    render_dashboard(registry, reports, latest_report)
with coverage_tab:
    render_coverage(registry)
with spending_tab:
    render_contract_spending(financial_view(
        ROOT, review_flag=os.environ.get("MIA_FINANCIAL_LOCAL_REVIEW"),
        server_address=st.get_option("server.address"),
        review_json=configured_financial_review(),
    ))

st.divider()
st.caption(INDEPENDENT_NOTICE)
