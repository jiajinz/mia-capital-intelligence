"""Read-only public directory for controlled MDAD source observations."""

import os
import sys
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mia_capital_intelligence.directory_queries import (  # noqa: E402
    DirectoryFilters, SORTS, format_usd, search_records, source_detail,
)
from mia_capital_intelligence.public_registry import AIRPORTS, PublicRegistry, load_registry  # noqa: E402
from mia_capital_intelligence.estimate_insights import (  # noqa: E402
    estimate_figure, largest_estimates, selected_source_ref,
)
from mia_capital_intelligence.contract_spending import FinancialView, financial_view  # noqa: E402

st.set_page_config(page_title="MIA Capital Intelligence", page_icon="✈", layout="wide")


@st.cache_resource(show_spinner=False)
def published_registry() -> PublicRegistry:
    """Cache immutable published inputs, with a fresh in-memory SQL query per search."""
    return load_registry(ROOT)


def report_label(source: dict) -> str:
    return f"{source['period_start']} to {source['period_end']} · {source['matter_id']}"


def profile_permalink(source_ref: str) -> str:
    return "?" + urlencode({"record": source_ref})


def render_detail(registry: PublicRegistry, source_ref: str) -> None:
    detail = source_detail(registry, source_ref)
    source = detail["source"]
    with st.container(border=True):
        st.caption(f"SOURCE RECORD · {detail['project_id']} · {source['matter_id']}")
        st.subheader(detail["project_name"])
        st.link_button("Open profile permalink", profile_permalink(detail["source_ref"]))
        st.link_button(
            f"Open official PDF · page {detail['pdf_page']}",
            detail["source_page_url"], type="primary",
        )
        st.write(
            f"This report lists **{detail['project_id']}** in its Capital Improvement Program. "
            "The information below describes this individual source record."
        )
        value, context = st.columns([1, 2], gap="large")
        with value:
            st.metric("Total estimated cost · reported USD", format_usd(detail["estimate_usd"]))
            st.caption("A planning estimate as reported, not actual spending or an approved contract budget.")
            st.write(f"**Airport**  {detail['airport_name']}")
            st.write("**Program**  Capital Improvement Program")
            st.caption("Detailed project type, status and milestones are not indexed.")
            st.write("**Construction progress**  Not available in the indexed fields")
            st.write("**Milestone dates**  Not available in the indexed fields")
        with context:
            st.write("**Source report**")
            st.write(source["title"])
            st.write(f"Report coverage · {source['period_start']} to {source['period_end']}")
            st.write(f"Memo · {source['memo_date']} · Board acceptance · {source['accepted_date']}")
            st.caption("Coverage follows the memorandum. The project-data snapshot date is unconfirmed.")
            st.write(f"PDF page {detail['pdf_page']} · printed {detail['printed_page']} · data row {detail['row_ordinal']}")
            st.caption(detail["validation_status"] + ".")
        with st.expander("Original wording and evidence"):
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
    st.subheader("Largest Reported Project Cost Estimates")
    st.write("Discover larger reported investments, then open a record to understand its source context.")
    sources = {row["matter_id"]: row for row in registry.catalog if row["indexed_record_count"]}
    report_col, airport_col, size_col = st.columns([2, 2, 1])
    with report_col:
        matter = st.selectbox("Chart source report", list(reversed(sources)),
                              format_func=lambda key: report_label(sources[key]), key="chart_report")
    with airport_col:
        airport = st.selectbox("Chart airport", [None, *AIRPORTS, "Unknown"], key="chart_airport",
                               format_func=lambda code: "All airports" if code is None else code)
    with size_col:
        limit = st.selectbox("Show largest", [5, 10, 20], index=1, key="chart_limit")
    keyword = st.text_input("Find within this chart", key="chart_search", placeholder="Project ID or keyword")
    ranking = largest_estimates(registry, matter, airport, keyword, limit)
    source = sources[matter]
    st.caption(
        f"Single report · {matter} · Exhibit B · Memo {source['memo_date']} · "
        f"Coverage {source['period_start']} to {source['period_end']}. "
        "The project-data snapshot date is unconfirmed."
    )
    st.caption(
        f"Showing {len(ranking.rows)} largest of {ranking.matching_count} matching source records "
        f"in {ranking.snapshot_count} indexed rows in this report; "
        f"{ranking.missing_count} matching records have unknown estimates and are excluded from ranking. "
        "This is a partial report population, not all airport projects."
    )
    if not ranking.rows:
        st.info("No known cost estimates match these chart filters. Try a different airport or keyword.")
        return
    # A filter-specific chart key prevents a previous chart's event selecting a new population.
    token = sha256(repr((matter, airport, keyword, limit)).encode()).hexdigest()[:16]
    event = st.plotly_chart(
        estimate_figure(ranking), width="stretch", key=f"estimates-{token}",
        on_select="rerun", selection_mode="points", config={"displayModeBar": False, "scrollZoom": False},
    )
    st.caption("Select a bar or use the selector to open the profile and evidence links below.")
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
    render_detail(registry, reference)
    with st.expander("Chart values and source pages"):
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
    st.write("Search publicly reported project records and open the original evidence.")
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
    st.caption(
        f"{len(results)} matching source records of {len(registry.records)} indexed records · "
        "Source program: Capital Improvement Program. Counts refer to report rows; cross-report identities remain unresolved."
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
    st.dataframe(
        frame, hide_index=True, height=min(330, 40 + 35 * len(results)), width="stretch",
        column_config={
            "Reported project description": st.column_config.TextColumn(width="large"),
            "Reporting period": st.column_config.TextColumn(width="medium"),
        },
    )
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


def render_coverage(registry: PublicRegistry) -> None:
    st.subheader("Sources & data coverage")
    st.caption("An independent data project. Underlying records are published by Miami-Dade County.")
    st.write(
        "Three official documents are cataloged. The directory indexes only Exhibit B in two infrastructure reports. "
        "This subset does not establish full airport project or capital-budget coverage."
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
    st.write("Explore reported expenditures for one contract in the sampled financial exhibits.")
    contracts = sorted({row.contract_id for row in view.rows})
    contract = st.selectbox("Contract", contracts, index=contracts.index("A19-MDAD-02"), key="spending_contract")
    rows = [row for row in view.rows if row.contract_id == contract]
    figure = go.Figure(go.Bar(
        x=[row.month_label for row in rows], y=[float(row.monthly_usd) for row in rows],
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
st.markdown("### Airport Infrastructure & Capital Projects Explorer")
st.caption("Explore project records and reported cost estimates. Spending history availability depends on financial review.")
st.write("Explore airport improvements, project investments, construction progress, and publicly reported financial information—all in one place.")
st.caption("Discover projects. Understand investments. Follow progress.")
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

st.caption("Use Open profile permalink on a source record to share its exact report version.")
st.caption(
    f"{len(registry.records)} source records · "
    f"{sum(row['indexed_record_count'] > 0 for row in registry.catalog)} partially indexed reports · "
    f"{len(registry.catalog)} cataloged documents · "
    "Source-reported estimates in USD"
)
directory_tab, insights_tab, coverage_tab, spending_tab = st.tabs([
    "Project directory", "Visual insights", "Sources & methodology", "Contract spending history",
])
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
    ))
st.divider()
st.caption(
    "Source observations retain their reporting context. Detailed status and milestone fields are not indexed in this slice. "
    "Candidate links provide navigation context; cross-report analytical comparisons require separate verification."
)
