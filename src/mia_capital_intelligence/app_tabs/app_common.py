"""Shared render helpers, notice text, cached loaders and query routing for the public explorer tabs."""

from datetime import date
from html import escape
from pathlib import Path
from urllib.parse import urlencode

import streamlit as st

from mia_capital_intelligence import public_registry, traffic_view
from mia_capital_intelligence.directory_queries import ESTIMATE_BANDS, format_usd, source_detail
from mia_capital_intelligence.estimate_insights import EstimateRanking
from mia_capital_intelligence.public_registry import AIRPORTS, PublicRegistry
from mia_capital_intelligence.traffic_view import TrafficSeries

ROOT = Path(__file__).resolve().parents[3]


PAGE_STYLE = """
    <style>
    @import url("https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap");
    .stApp, .stApp p, .stApp label, .stApp li, .stApp td, .stApp th, .stApp input, .stApp textarea,
    .stApp [data-testid="stMarkdownContainer"], .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
      font-family: Roboto, "Helvetica Neue", sans-serif;
    }
    .stApp h1, .stApp h2, .stApp h3 { color:#012851; font-weight:700; }
    .stApp [data-testid="stMarkdownContainer"] a { color:#337AB7; }
    </style>
"""


@st.cache_resource(show_spinner=False)
def published_registry() -> PublicRegistry:
    """Cache immutable published inputs, with a fresh in-memory SQL query per search."""
    return public_registry.load_registry(ROOT)


@st.cache_resource(show_spinner=False)
def published_traffic() -> TrafficSeries:
    return traffic_view.load_traffic_series()


def report_label(source: dict) -> str:
    return f"{report_period(source['period_start'], source['period_end'])} · {source['matter_id']}"


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


def render_record_links(detail: dict, reference: str) -> None:
    """One caption line of plain links: the official PDF page and this record's permalink."""
    st.caption(
        f"[Open official PDF · page {detail['pdf_page']}]({detail['source_page_url']}) · "
        f"[Link to this record]({profile_permalink(reference)})"
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
            render_record_links(detail, reference)
            if detail["project_brief"] != detail["project_name"]:
                st.markdown("**Project brief**")
                st.html(f'<p class="mia-ranked-brief">{escape(detail["project_brief"])}</p>')
            render_project_brief(detail, expanded=False, include_brief=False)
        return
    with st.container(border=True):
        st.caption(f"{detail['project_id']} · {detail['airport_name']} · {report_label(source)}")
        st.subheader(detail["project_name"])
        st.metric("Reported total cost estimate · USD", format_usd(detail["estimate_usd"]))
        render_record_links(detail, reference)
        st.write("**Scope as described in the report**")
        st.text(detail["description_raw"])


def render_detail(registry: PublicRegistry, source_ref: str) -> None:
    detail = source_detail(registry, source_ref)
    source = detail["source"]
    with st.container(border=True):
        st.subheader(detail["project_name"])
        period = report_period(source["period_start"], source["period_end"])
        st.caption(f"{detail['project_id']} · {detail['airport_name']} · {period}")
        st.metric("Reported total cost estimate · USD", format_usd(detail["estimate_usd"]))
        render_record_links(detail, detail["source_ref"])
        st.html(
            '<p class="mia-source-hash" style="margin:0; overflow-wrap:anywhere; font-size:.875rem; color:#3F5161">'
            f'Source document SHA-256 · <code>{escape(source["sha256"])}</code></p>'
        )
        render_project_brief(detail, expanded=True)
        with st.expander("Report and source details"):
            st.write(source["title"])
            st.caption(f"{detail['reporting_agency']} · Report {source['matter_id']} · Exhibit B")
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


def render_estimate_distribution(
    ranking: EstimateRanking, source: dict, *, show_context: bool = True,
) -> None:
    """Display-only counts per estimate range. The bars are not links; the range list is a separate control."""
    known_count = ranking.matching_count - ranking.missing_count
    if not known_count:
        st.info("No indexed records with a known estimate match this report.")
        return
    if show_context:
        st.markdown(f"**{ranking.band_counts[0]} of {ranking.matching_count} matching records** show estimates under $10 million.")
    rows = []
    for band, count in zip(ESTIMATE_BANDS, ranking.band_counts, strict=True):
        label = f'<span class="mia-band-name">{escape(band)}</span><span class="mia-band-count">{count}</span>'
        track = f'<span class="mia-band-track" aria-hidden="true"><i style="width:{count / known_count:.2%}"></i></span>'
        rows.append(f'<div class="mia-band-row"><span class="mia-band-label">{label}</span>{track}</div>')
    st.html('''
        <style>
        .mia-estimate-bands { display:grid; gap:.35rem; max-width:52rem }
        .mia-band-row { display:block; padding:.4rem .55rem; font-size:1rem; line-height:1.4;
          font-weight:400; color:#333333; border:1px solid transparent; border-radius:.35rem }
        .mia-band-label { display:flex; justify-content:space-between; align-items:baseline; gap:1rem }
        .mia-band-name { font-weight:400 }
        .mia-band-count { font-weight:700; font-variant-numeric:tabular-nums; text-align:right; color:#012851 }
        .mia-band-track { display:block; margin-top:.2rem; height:.45rem; background:#E4EAF0; border-radius:2px }
        .mia-band-track i { display:block; height:100%; background:#007BB6; border-radius:2px }
        </style>
        <div class="mia-estimate-bands" role="group" aria-label="Source record counts by estimate range in USD">'''
        + "".join(rows) + "</div>")
    if show_context:
        st.caption(
            f"Miami-Dade County · Report {source['matter_id']} · {known_count} records with estimates · "
            f"{ranking.missing_count} without. Select a range to see the records behind it."
        )


CLOSED_SPENDING_MESSAGES = {
    "pending_review": "Contract spending: pending review.",
    "stale_review": "Contract spending: pending review. The review on file is for an earlier version of the figures.",
    "invalid_review": "Contract spending: pending review. The review on file did not pass validation.",
    "invalid_input": "Contract spending: unavailable until the figures are rebuilt and reviewed.",
}


SECTIONS = ("Overview", "Projects", "Traffic", "Spending", "Sources & Coverage")
SECTION_OVERVIEW, SECTION_PROJECTS, SECTION_TRAFFIC, SECTION_SPENDING, SECTION_COVERAGE = SECTIONS
SECTION_KEY = "section"

# Plain facts only, shown at the bottom of the Traffic section.
TRAFFIC_METHOD_NOTE = (
    "**Source.** Monthly traffic reports published by Miami International Airport. Early months come from monthly "
    "web pages and later months from PDF reports. The table gives the source file and PDF page for each value. "
    "PDF page numbers count from 1.",
    "**Series.** Passenger movements are deplaned plus enplaned. Cargo is total cargo tons. Both are combined totals "
    "for international and domestic traffic. The series holds 199 reported months, from January 2010 to September 2026.",
    "**2010-07** (July 2010) has no source page, so no value is shown.",
    "**2013-06** (June 2013) is held. Its year-to-date totals did not pass an internal check, so no value is shown.",
    "**March 2025** comes from a revised report. Its first-published version was not obtained.",
    "**March 2020 to December 2021** is the pandemic period. Values inside it are shown as published, without adjustment.",
    "December 2017, October 2018 and June 2022 appear only as the prior-year column of a later report. The table labels them.",
    "**Reference forecast.** Each month from October 2026 to September 2027 equals the same month of the prior year. It is a benchmark, not a model. Its error is measured on past months where both values exist. "
    "Model forecasts are not published.",
    "The Traffic section does not link traffic to projects or contracts.",
)


def render_record_page(registry: PublicRegistry) -> None:
    st.title("MIA Capital Intelligence")
    requested = st.query_params.get_all("record")
    st.link_button("Browse project records", "?")
    if len(requested) == 1 and any(row.source_ref == requested[0] for row in registry.records):
        render_detail(registry, requested[0])
    else:
        st.warning("This record link is outside the current registry version or is invalid. Open the directory to choose an available record.")


def open_section(name: str) -> None:
    """Callback helper: move the visitor to another top-level section."""
    st.session_state[SECTION_KEY] = name


def open_report(matter_id: str) -> None:
    """Callback helper: open one source document in Sources & Coverage."""
    st.session_state["coverage_source"] = matter_id
    open_section(SECTION_COVERAGE)


def initialize_explore_route(reports: dict) -> None:
    """Honor the same-report estimate links: ?report=...&range=... opens the Projects list for that range."""
    report_route = st.query_params.get_all("report")
    range_route = st.query_params.get_all("range")
    airport_route = st.query_params.get_all("airport")
    if not st.session_state.get("explore_initialized"):
        if (len(report_route) == len(range_route) == 1
                and report_route[0] in reports and range_route[0] in ESTIMATE_BANDS):
            st.session_state.update(section=SECTION_PROJECTS, source_report=report_route[0],
                                    estimate_range=range_route[0])
            if len(airport_route) == 1 and airport_route[0] in (*AIRPORTS, "Unknown"):
                st.session_state.update(airport=airport_route[0], chart_airport=airport_route[0])
        st.session_state["explore_initialized"] = True
