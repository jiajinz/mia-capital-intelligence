"""Traffic section: monthly passenger and cargo series with year-on-year comparison."""

import pandas as pd
import streamlit as st

from mia_capital_intelligence.app_tabs.app_common import TRAFFIC_METHOD_NOTE, published_traffic
from mia_capital_intelligence.traffic_view import (
    LAST_PERIOD, MONTH_NAMES, TrafficSeries, all_years_figure, comparable_years, reference_errors, reference_figure,
    reference_forecast, series_years, traffic_figure, year_comparison, year_figure,
)


# About five rows are visible; the rest scroll inside the table.
TABLE_HEIGHT = 230

def traffic_cell(series: TrafficSeries, period: str, value_of) -> str:
    """Name the state of one month without guessing: a value, a gap, held, or outside the series."""
    month = series.by_period().get(period)
    if month is not None:
        return f"{value_of(month).value:,}"
    for item in series.unavailable:
        if item.period == period:
            return "Gap (no value)" if item.status == "gap" else "Held (no value)"
    return "Not in series" if period > LAST_PERIOD else "No value"


def render_prior_year(series: TrafficSeries, measure: str, value_of) -> None:
    years = comparable_years(series)
    year = st.radio("Year, compared with the prior year", years, index=years.index(2025), format_func=str,
                    key="traffic_year", horizontal=True)
    st.plotly_chart(year_figure(series, year, measure), width="stretch",
                    config={"displayModeBar": False, "scrollZoom": False})
    rows = []
    for change in year_comparison(series, year, measure):
        period_prior = f"{year - 1}-{change.month:02d}"
        period_current = f"{year}-{change.month:02d}"
        rows.append({
            "Month": MONTH_NAMES[change.month - 1],
            f"{year - 1}": traffic_cell(series, period_prior, value_of),
            f"{year}": traffic_cell(series, period_current, value_of),
            "Change": "" if change.change is None else f"{change.change:+,}",
            "Change (%)": "" if change.percent is None else f"{change.percent:+.1f}%",
        })
    with st.expander("Monthly figures"):
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=TABLE_HEIGHT)
        st.caption(
            "Change compares each month with the same month of the prior year. Blank change means one of the two "
            "months has no value. Percent changes are rounded to one decimal place."
        )


def render_all_years(series: TrafficSeries, measure: str, value_of) -> None:
    all_years = series_years(series)
    chosen = st.multiselect("Years shown", all_years, default=[year for year in all_years if year >= 2020],
                            format_func=str, key="traffic_all_years")
    if not chosen:
        st.info("Choose at least one year to show its line.")
        return
    st.plotly_chart(all_years_figure(series, tuple(chosen), measure), width="stretch",
                    config={"displayModeBar": False, "scrollZoom": False})
    table = {"Month": list(MONTH_NAMES)}
    for year in sorted(chosen):
        table[str(year)] = [traffic_cell(series, f"{year}-{month:02d}", value_of) for month in range(1, 13)]
    with st.expander("Monthly figures"):
        st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch", height=TABLE_HEIGHT)


def render_reference_forecast(series: TrafficSeries, measure: str) -> None:
    st.subheader("Reference forecast")
    st.caption(
        "A benchmark, not a model. Each month from October 2026 to September 2027 equals the same month of the "
        "prior year. Model forecasts are not published."
    )
    st.plotly_chart(reference_figure(series, measure), width="stretch",
                    config={"displayModeBar": False, "scrollZoom": False})
    errors = {error.label: error for error in reference_errors(series, measure)}
    normal = [errors["2011 to 2019"], errors["2022 to 2026"]]
    error_text = " · ".join(f"{error.label}: {error.mape}%" for error in normal)
    st.caption(f"Error on past months, mean absolute percentage error · {error_text}. The pandemic period is in the table.")
    rows = []
    for row in reference_forecast(series, measure):
        rows.append({
            "Month": row.period,
            "Reference value": "No value" if row.value is None else f"{row.value:,}",
            "Copied from": row.source_period,
        })
    with st.expander("Reference values and error"):
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=TABLE_HEIGHT)
        st.caption(
            "Error is measured on months where both the month and the same month of the prior year have values. "
            "The pandemic period is shown separately because traffic fell sharply and the percentages are large."
        )


def render_source_table(series: TrafficSeries) -> None:
    unavailable = {item.period: item for item in series.unavailable}
    by_period = series.by_period()
    table = []
    for period in series.all_periods():
        month = by_period.get(period)
        if month is None:
            item = unavailable[period]
            table.append({
                "Month": period, "Passenger movements": "Gap (no value)" if item.status == "gap" else "Held (no value)",
                "Passenger source file": "", "Passenger PDF page": "",
                "Cargo tons": "Gap (no value)" if item.status == "gap" else "Held (no value)",
                "Cargo source file": "", "Cargo PDF page": "",
                "Notes": item.reason,
            })
            continue
        notes = list(dict.fromkeys(note for note in (month.passengers.note, month.cargo_tons.note) if note))
        table.append({
            "Month": period,
            "Passenger movements": f"{month.passengers.value:,}",
            "Passenger source file": month.passengers.source_file,
            "Passenger PDF page": "HTML page" if month.passengers.pdf_page is None else str(month.passengers.pdf_page),
            "Cargo tons": f"{month.cargo_tons.value:,}",
            "Cargo source file": month.cargo_tons.source_file,
            "Cargo PDF page": "HTML page" if month.cargo_tons.pdf_page is None else str(month.cargo_tons.pdf_page),
            "Notes": "; ".join(notes) if notes else "",
        })
    with st.expander("Source data"):
        st.caption(
            f"{len(series.months)} months with admitted values · {len(unavailable)} months without a value · "
            "PDF page numbers count from 1 · HTML pages have no PDF page."
        )
        st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch", height=TABLE_HEIGHT)


def render_traffic(series: TrafficSeries) -> None:
    st.header("Monthly airport traffic")
    st.subheader("Monthly passenger movements, 2010 to 2026")
    st.caption(
        "Each point is one reported month. Dotted lines mark months without a value. The shaded band marks "
        "March 2020 to December 2021. Open diamonds mark values from a revised report. The lower panel shows "
        "monthly total cargo tons."
    )
    st.plotly_chart(traffic_figure(series), width="stretch", config={"displayModeBar": False, "scrollZoom": False})

    st.subheader("Compare years")
    view = st.radio("View", ("Against the prior year", "All years together"), horizontal=True, key="traffic_view")
    measure_label = st.radio("Measure", ("Passengers", "Cargo tons"), horizontal=True, key="traffic_measure")
    measure = "passengers" if measure_label == "Passengers" else "cargo_tons"
    value_of = (lambda month: month.passengers) if measure == "passengers" else (lambda month: month.cargo_tons)
    if view == "All years together":
        render_all_years(series, measure, value_of)
    else:
        render_prior_year(series, measure, value_of)
    render_reference_forecast(series, measure)
    render_source_table(series)

    with st.expander("About these figures"):
        for paragraph in TRAFFIC_METHOD_NOTE:
            st.markdown(paragraph)


def render_traffic_tab() -> None:
    try:
        series = published_traffic()
    except (ValueError, OSError, KeyError):
        st.header("Monthly airport traffic")
        st.error("The traffic data could not be validated. The Traffic tab is unavailable until the data is repaired.")
        return
    render_traffic(series)
