"""Read-only public directory for controlled MDAD source observations."""

import os
import sys
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
    EstimateRanking, estimate_figure, largest_estimates, selected_source_ref,
)
from mia_capital_intelligence.contract_spending import FinancialView, financial_view  # noqa: E402

CASE_REFS = (
    "260526:eaf845f4fb746a69940f38fe4655d27b56ab42effdbf9cfdd1dbc746a0fba878:B:11:63",
    "261402:84751b451da8b7d5e06cad6b1c24c870e563de5669c5f07325033c446bbaeb2a:B:12:65",
    "260526:eaf845f4fb746a69940f38fe4655d27b56ab42effdbf9cfdd1dbc746a0fba878:B:11:64",
)

st.set_page_config(page_title="MIA Capital Intelligence", page_icon="✈", layout="wide")


@st.cache_resource(show_spinner=False)
def published_registry() -> PublicRegistry:
    """Cache immutable published inputs, with a fresh in-memory SQL query per search."""
    return load_registry(ROOT)


def report_label(source: dict) -> str:
    return f"{source['period_start']} to {source['period_end']} · {source['matter_id']}"


def profile_permalink(source_ref: str) -> str:
    return "?" + urlencode({"record": source_ref})


def render_project_brief(detail: dict, *, expanded: bool) -> None:
    with st.expander("Project brief and delivery team", expanded=expanded):
        st.html(f'<p style="margin:0; overflow-wrap:anywhere">{escape(detail["project_brief"])}</p>')
        st.markdown(f"**Reporting agency** · {detail['reporting_agency']}")
        lead = detail["project_lead"] or "Not listed in the indexed record"
        contractor = detail["awarded_contractor"] or "Unverified in the indexed sources"
        st.markdown(f"**Project lead** · {lead}")
        st.markdown(f"**Awarded contractor** · {contractor}")


def render_record_summary(registry: PublicRegistry, reference: str, *, show_scope: bool = False) -> None:
    detail = source_detail(registry, reference)
    with st.container(border=True):
        st.caption(f"{detail['project_id']} · {detail['airport_name']} · {report_label(detail['source'])}")
        st.subheader(detail["project_name"])
        st.metric("Reported total cost estimate · USD", format_usd(detail["estimate_usd"]))
        if show_scope:
            st.write("**Scope as described in the report**")
            st.text(detail["description_raw"])
        st.link_button(f"Open official PDF · page {detail['pdf_page']}", detail["source_page_url"], type="primary")
        st.link_button("Open profile permalink", profile_permalink(reference))
        if not show_scope:
            render_project_brief(detail, expanded=False)


def render_estimate_distribution(
    ranking: EstimateRanking, source: dict,
) -> None:
    known_count = ranking.snapshot_count - ranking.missing_count
    if not known_count:
        st.info("This report has no indexed records with a known estimate.")
        return
    st.markdown(f"**{ranking.band_counts[0]} of {ranking.snapshot_count} indexed records** show estimates under $10 million.")
    bars = []
    for band, count in zip(ESTIMATE_BANDS, ranking.band_counts, strict=True):
        route = "?" + urlencode({"report": ranking.matter_id, "range": band})
        label = f"{escape(band)} <strong>{count}</strong>"
        track = f'<span class="mia-band-track" aria-hidden="true"><i style="width:{count / known_count:.2%}"></i></span>'
        content = f'<span class="mia-band-label">{label}</span>{track}'
        if count:
            bars.append(f'<a href="{escape(route)}" target="_blank" rel="noopener" '
                        f'aria-label="{escape(band)} · {count} records">{content}</a>')
        else:
            bars.append(f'<div class="mia-band-zero">{content}</div>')
    st.html('''
        <style>
        .mia-estimate-bands { display:grid; gap:.35rem; max-width:52rem }
        .mia-estimate-bands a, .mia-band-zero { display:block; padding:.4rem .55rem;
          color:#152D36; text-decoration:none; border:1px solid transparent; border-radius:.35rem }
        .mia-estimate-bands a:hover { background:#F4F7F8; text-decoration:underline }
        .mia-estimate-bands a:focus-visible { outline:2px solid #1E6358 }
        .mia-band-label { display:flex; justify-content:space-between; gap:1rem }
        .mia-band-label strong { font-variant-numeric:tabular-nums }
        .mia-band-track { display:block; margin-top:.2rem; height:.45rem; background:#E6EFED; border-radius:2px }
        .mia-band-track i { display:block; height:100%; background:#1E6358; border-radius:2px }
        </style>
        <div class="mia-estimate-bands" role="group" aria-label="Source record counts by estimate range in USD">'''
        + "".join(bars) + "</div>")
    st.caption(
        f"Miami-Dade County · Matter {source['matter_id']} · {known_count} records with estimates · "
        f"{ranking.missing_count} without. Select a range to see the records behind it."
    )


def render_detail(registry: PublicRegistry, source_ref: str) -> None:
    detail = source_detail(registry, source_ref)
    source = detail["source"]
    with st.container(border=True):
        st.caption(f"{detail['project_id']} · {detail['airport_name']} · {report_label(source)}")
        st.subheader(detail["project_name"])
        st.metric("Reported total cost estimate · USD", format_usd(detail["estimate_usd"]))
        st.link_button(
            f"Open official PDF · page {detail['pdf_page']}",
            detail["source_page_url"], type="primary",
        )
        st.link_button("Open profile permalink", profile_permalink(detail["source_ref"]))
        render_project_brief(detail, expanded=True)
        with st.expander("Original wording and evidence"):
            st.write(source["title"])
            st.write(f"Memo · {source['memo_date']} · Board acceptance · {source['accepted_date']}")
            st.caption("Coverage follows the memorandum. The project-data snapshot date is unconfirmed.")
            st.write(f"PDF page {detail['pdf_page']} · printed {detail['printed_page']} · data row {detail['row_ordinal']}")
            st.caption(detail["validation_status"] + ".")
            st.caption("The reported amount is a planning estimate. Detailed project type, status and milestones are not indexed.")
            st.write("**Original project description**")
            st.text(detail["description_raw"])
            st.write("**Original estimate header and cell**")
            st.text(detail["estimate_header"] + "\n" + detail["estimate_raw"])
            st.caption(detail["description_status"] + ".")
            st.caption(detail["airport_evidence"] + ".")
            st.write(f"Printed fiscal-year caption · {source['matter_id']}")
            caption = (
                "FY 2024- 2025; for Period October 2025 - December 2025"
                if source["matter_id"] == "260526" else "FY 2025- 2026"
            )
            st.text(caption)
            st.write("**Document SHA-256**")
            st.code(source["sha256"], language=None)
            st.write("**Versioned source-row reference**")
            st.code(detail["source_ref"], language=None)
            st.caption("The project identity across documents is unresolved. This profile represents one source record.")
        if detail["candidate_source_refs"]:
            with st.expander("Same ID in another report · identity unresolved"):
                st.write(
                    "The shared ID is a candidate association. These records remain separate observations. "
                    "Their engineering scope and estimate basis require additional evidence before comparison."
                )
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


def render_insights(registry: PublicRegistry) -> None:
    st.subheader("How large are the reported estimates?")
    sources = {row["matter_id"]: row for row in registry.catalog if row["indexed_record_count"]}
    matter = st.selectbox("Report period", list(reversed(sources)),
                          format_func=lambda key: report_label(sources[key]), key="chart_report")
    source = sources[matter]
    render_estimate_distribution(largest_estimates(registry, matter), source)
    with st.expander("See the largest estimates"):
        render_estimate_ranking(registry, matter, source)


def render_estimate_ranking(registry: PublicRegistry, matter: str, source: dict) -> None:
    airport_col, size_col = st.columns([2, 1])
    with airport_col:
        airport = st.selectbox("Chart airport", [None, *AIRPORTS, "Unknown"], key="chart_airport",
                               format_func=lambda code: "All airports" if code is None else code)
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
    chart, evidence = st.columns([2, 1], gap="medium")
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


def render_directory(registry: PublicRegistry) -> None:
    sources = {row["matter_id"]: row for row in registry.catalog}
    st.subheader("Project directory")
    query = st.text_input(
        "Search project ID, name or facility",
        placeholder="Try CA176A, chiller, boarding bridges or TMB",
        key="search",
    )
    airport_column, report_column, sort_column = st.columns([1, 2, 2])
    with airport_column:
        airport = st.selectbox(
            "Airport", [None, *AIRPORTS, "Unknown"], key="airport",
            format_func=lambda code: (
                "All airports" if code is None else
                "Unknown airport" if code == "Unknown" else f"{code} · {AIRPORTS[code]}"
            ),
        )
    with report_column:
        matter = st.selectbox(
            "Source report", [None, *[key for key, row in sources.items() if row["indexed_record_count"]]],
            format_func=lambda key: "All indexed reports" if key is None else report_label(sources[key]),
            key="source_report",
        )
    with sort_column:
        sort = st.selectbox("Sort records", list(SORTS), key="sort")
    results = search_records(registry, DirectoryFilters(query, airport, matter, sort))
    if matter is not None:
        band = st.selectbox(
            "Reported estimate range", [None, *ESTIMATE_BANDS], key="estimate_range",
            format_func=lambda value: value or "All estimates",
        )
        if band is not None:
            results = [row for row in results if estimate_band(row["estimate_usd"]) == band]
    indexed_count = sources[matter]["indexed_record_count"] if matter else len(registry.records)
    st.caption(
        f"{len(results)} matching source records of {indexed_count} indexed records."
    )
    if not results:
        st.info("No source records match these filters. Try a shorter keyword or select all airports and reports.")
        return
    frame = pd.DataFrame([
        {"Project ID": row["project_id"], "Reported project description": row["project_name"],
         "Airport": row["airport_code"] or "Unknown",
         "Reporting period": f"{row['period_start']} to {row['period_end']}",
         "Reported estimate (USD)": format_usd(row["estimate_usd"]),
         "Source": row["matter_id"], "PDF page": row["pdf_page"]}
        for row in results
    ])
    refs = [row["source_ref"] for row in results]
    by_ref = {row["source_ref"]: row for row in results}
    selected = st.selectbox(
        "Open a source record", refs,
        format_func=lambda ref: (
            f"{by_ref[ref]['project_id']} · {by_ref[ref]['matter_id']} · "
            f"{by_ref[ref]['project_name'][:110]}"
        ),
        key="selected_record",
    )
    render_detail(registry, selected)
    with st.expander("View matching records"):
        st.dataframe(
            frame, hide_index=True, height=min(330, 40 + 35 * len(results)), width="stretch",
            column_config={
                "Reported project description": st.column_config.TextColumn(width="large"),
                "Reporting period": st.column_config.TextColumn(width="medium"),
            },
        )
    with st.expander("Compare two records from one report"):
        if matter is None or len(refs) < 2:
            st.caption("Select one source report and use filters that leave at least two records.")
        else:
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


def render_coverage(registry: PublicRegistry) -> None:
    st.subheader("Sources & data coverage")
    st.caption("An independent data project. Underlying records are published by Miami-Dade County.")
    if set(CASE_REFS).issubset(row.source_ref for row in registry.records):
        with st.expander("Case study · Concourse D west extension"):
            st.markdown("#### What do the two reports establish?")
            st.write(
                "Both reports list T180B with the same building expansion and apron description. "
                "The earlier report separately lists T180D for D60 apron and utilities. "
                "How that scope was allocated, and whether the two T180B estimates use the same basis, "
                "remain open questions."
            )
            st.caption("The two estimates are shown as source observations. Scope comparability is awaiting verification.")
            for column, reference in zip(st.columns(2), CASE_REFS[:2], strict=True):
                with column:
                    render_record_summary(registry, reference, show_scope=True)
            earlier_apron = source_detail(registry, CASE_REFS[2])
            st.link_button("Open the earlier T180D source record", profile_permalink(earlier_apron["source_ref"]))
    st.write(
        f"The directory contains {len(registry.records)} source records from the indexed portions of two reports. "
        "Cross-report identities remain unresolved."
    )
    st.dataframe(pd.DataFrame([
        {"Matter": row["matter_id"], "Report coverage": f"{row['period_start']} to {row['period_end']}",
         "Indexed records": row["indexed_record_count"], "Indexing coverage": row["indexing_status"]}
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
        st.write(f"**Indexed records**  {source['indexed_record_count']} · {source['indexing_status']}")
        st.write(source["coverage_limit"])
        st.write(f"**Validation coverage**  {source['validation_status']}")
        if source["indexed_record_count"]:
            st.caption(
                "Original file identity was verified at registry build. Descriptions retain extracted source wording. "
                "Independent controls cover project IDs and estimates; scope and cross-report identity remain under review."
            )
        else:
            st.caption("Original file identity was verified at registry build. Its project rows are outside this public index.")
        st.write(f"**Reporting period**  {source['period_start']} to {source['period_end']}")
        st.write(f"**Memo date**  {source['memo_date']} · **Board acceptance**  {source['accepted_date']}")
        st.caption("The first public posting date and project-data freeze dates are unconfirmed.")
        pages = ", ".join(map(str, source["indexed_pdf_pages"])) or "None"
        st.write(f"**Indexed PDF pages**  {pages} · **Document pages**  {source['page_count']}")
        st.link_button("Open official source document", source["url"], type="primary")
        st.link_button("Open county legislative record", source["matter_url"])
        with st.expander("Document version and verification"):
            st.code(source["sha256"], language=None)
            st.write(f"SHA-256 · {source['size_bytes']:,} source bytes · matter {matter}")


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
        if view.status == "invalid_input":
            st.warning("Contract spending is unavailable because the financial input could not be validated.")
        elif view.status == "pending_review":
            st.info("Contract spending is pending named independent review.")
        else:
            st.warning("Contract spending is unavailable until a valid review for this financial input is recorded.")
        return
    if view.local_review and view.status != "approved":
        st.warning("Local review preview · Named independent review pending. Financial values are awaiting sign-off.")
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
        marker_color="#1E6358",
    ))
    figure.update_layout(
        title="Reported monthly expenditures", height=320, margin=dict(l=12, r=18, t=55, b=32),
        xaxis_title="Reported month", yaxis_title="Expenditures (USD)",
        yaxis_tickprefix="$", yaxis_rangemode="tozero", showlegend=False,
    )
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
        st.caption("The accounting cutoff and cash or accrual basis are unknown. Contract-to-project links are unverified.")
        for row in rows:
            st.write(f"**{row.month_label}** · {row.raw_contract} · {row.printed_page} row {row.row_ordinal}")
            st.link_button(f"Open {row.month_label} financial PDF · page {row.financial_page}", row.financial_url)
            st.link_button(f"Open {row.month_label} summary · page {row.summary_page} row {row.summary_row_ordinal}", row.summary_url)
            if row.monthly_dash_corroborated:
                st.caption("The summary explicitly reports $0.00 for the financial table's monthly dash.")
        if contract == "E20-MDAD-03":
            st.caption("The same-issue summaries use E20-MDAD-03. The financial tables print E20-MDAD--03.")
        if contract == "A19-MDAD-01":
            st.caption("Airport attribution is unresolved because the financial and summary descriptions differ.")


st.title("MIA Capital Intelligence")
st.caption("Airport Infrastructure & Capital Projects Explorer")
try:
    registry = published_registry()
except (ValueError, OSError, KeyError):
    st.error("The published data could not be validated. Project records are unavailable until the data is repaired.")
    st.stop()

if "record" in st.query_params:
    requested = st.query_params.get_all("record")
    st.link_button("Browse project records", "?")
    if len(requested) == 1 and any(row.source_ref == requested[0] for row in registry.records):
        render_detail(registry, requested[0])
    else:
        st.warning("This record link is outside the current registry version or is invalid. Open the directory to choose an available record.")
    st.stop()

reports = {source["matter_id"] for source in registry.catalog if source["indexed_record_count"]}
report_route = st.query_params.get_all("report")
range_route = st.query_params.get_all("range")
browse_range = (len(report_route) == len(range_route) == 1
                and report_route[0] in reports and range_route[0] in ESTIMATE_BANDS)
if browse_range:
    st.session_state.setdefault("source_report", report_route[0])
    st.session_state.setdefault("estimate_range", range_route[0])

directory_tab, insights_tab, coverage_tab, spending_tab = st.tabs([
    "Project directory", "Visual insights", "Sources & methodology", "Contract spending history",
], default="Project directory" if browse_range else "Visual insights")
with directory_tab:
    render_directory(registry)
with insights_tab:
    render_insights(registry)
with coverage_tab:
    render_coverage(registry)
with spending_tab:
    render_contract_spending(financial_view(
        ROOT, review_flag=os.environ.get("MIA_FINANCIAL_LOCAL_REVIEW"),
        server_address=st.get_option("server.address"),
        review_json=configured_financial_review(),
    ))
