"""Spending tab: contract expenditure history, shown only when the financial review gate allows it."""

import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from mia_capital_intelligence.app_tabs.app_common import CLOSED_SPENDING_MESSAGES, open_section
from mia_capital_intelligence import contract_spending
from mia_capital_intelligence.contract_spending import FinancialView
from mia_capital_intelligence.estimate_insights import apply_chart_theme

DEFAULT_CONTRACT = "A19-MDAD-02"


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


def financial_view_for_app(root: Path) -> FinancialView:
    return contract_spending.financial_view(
        root, review_flag=os.environ.get("MIA_FINANCIAL_LOCAL_REVIEW"),
        server_address=st.get_option("server.address"),
        review_json=configured_financial_review(),
    )


def render_spending_summary(root: Path) -> None:
    """Overview panel: the same gate as the Spending section; a closed gate shows only its status message."""
    view = financial_view_for_app(root)
    if not view.rows:
        st.info(CLOSED_SPENDING_MESSAGES.get(view.status, "Contract spending data is currently unavailable."))
        return
    if view.local_review and view.status != "approved":
        st.warning("Local review preview.")
    st.caption("July–September 2026 · Four contracts · Three monthly Aviation Capital Program reports")
    latest = {}
    for row in view.rows:
        latest[row.contract_id] = row
    st.dataframe(pd.DataFrame([
        {"Contract": contract, "Reported through September": f"${row.cumulative_usd:,.2f}"}
        for contract, row in latest.items()
    ]), hide_index=True, width="stretch")
    st.button("Open the Spending section", key="open-spending", on_click=open_section, args=("Spending",))


def render_contract_spending(view: FinancialView) -> None:
    st.subheader("Contract spending history")
    if not view.rows:
        st.info(CLOSED_SPENDING_MESSAGES.get(view.status, "Contract spending data is currently unavailable."))
        return
    if view.local_review and view.status != "approved":
        st.warning("Local review preview.")
    st.caption("July–September 2026 · Four contracts · Three monthly Aviation Capital Program reports")
    contracts = sorted({row.contract_id for row in view.rows})
    contract = st.radio("Contract", contracts, index=contracts.index(DEFAULT_CONTRACT), key="spending_contract",
                        horizontal=True)
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


def render_spending_tab(root: Path) -> None:
    render_contract_spending(financial_view_for_app(root))
