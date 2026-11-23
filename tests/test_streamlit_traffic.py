"""Streamlit's simulated runtime checks the read-only Traffic tab."""

import json
import re
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

from mia_capital_intelligence import traffic_view

APP = Path(__file__).resolve().parents[1] / "streamlit_app.py"
TRAFFIC_TAB = 4


def app():
    result = AppTest.from_file(APP, default_timeout=30).run()
    assert not result.exception
    return result


def traffic(result):
    return result.tabs[TRAFFIC_TAB]


def tab_text(tab) -> str:
    parts = [str(element.value) for kind in ("header", "subheader", "markdown", "caption") for element in getattr(tab, kind)]
    parts.extend(frame.value.to_string() for frame in tab.dataframe)
    parts.extend(chart.proto.spec for chart in tab.get("plotly_chart"))
    parts.extend(str(element.value) for element in tab.info)
    parts.extend(str(element.value) for element in tab.warning)
    return "\n".join(parts)


def chart_spec(tab, index: int = 0) -> dict:
    return json.loads(tab.get("plotly_chart")[index].proto.spec)


def chart_annotations(tab) -> list[str]:
    return [item.get("text", "") for item in chart_spec(tab)["layout"].get("annotations", [])]


def test_traffic_tab_renders_its_sections_in_order():
    result = app()
    assert [tab.label for tab in result.tabs][TRAFFIC_TAB] == "Traffic"
    tab = traffic(result)
    assert tab.header[0].value == "Monthly airport traffic"
    assert [item.value for item in tab.subheader] == [
        "Method note", "Monthly passengers and cargo", "Year-on-year comparison", "Exact values and sources",
    ]
    assert len(tab.get("plotly_chart")) == 2
    assert not tab.error


def test_method_note_states_series_source_gaps_break_and_limits_before_the_chart():
    tab = traffic(app())
    notes = [item.value for item in tab.markdown]
    assert notes[0].startswith("**What the series is.**")
    for lead in ("**Where it comes from.**", "**What is missing.**", "**The pandemic break.**",
                 "**What this tab does not do.**"):
        assert any(note.startswith(lead) for note in notes), lead
    text = tab_text(tab)
    assert "199 reported months" in text
    assert "PDF page numbers count from 1" in text
    assert "July 2010 is a gap" in text and "June 2013 is held" in text


def test_chart_labels_both_unavailable_months_and_the_pandemic_break():
    tab = traffic(app())
    annotations = chart_annotations(tab)
    assert "Gap 2010-07" in annotations
    assert "Held 2013-06" in annotations
    assert "Pandemic break, Mar 2020 to Dec 2021" in annotations
    shapes = chart_spec(tab)["layout"].get("shapes", [])
    assert any(shape.get("x0") == "2020-03-01" and shape.get("x1") == "2022-01-01" for shape in shapes)
    assert chart_spec(tab)["layout"]["xaxis"]["range"] == ["2009-12-15", "2026-10-15"]


def test_tab_has_no_forecast_projection_cost_or_financial_text():
    tab = traffic(app())
    text = tab_text(tab)
    assert not re.search(r"forecast|projection|predict|outlook|\bcost|spending|\$", text, re.IGNORECASE)


def test_exact_table_gives_source_file_and_pdf_page_for_each_value():
    tab = traffic(app())
    table = tab.dataframe[1].value
    assert len(table) == 201
    rows = {row["Month"]: row for _, row in table.iterrows()}
    january_2024 = rows["2024-01"]
    assert january_2024["Passenger movements"] == "5,035,404"
    assert january_2024["Passenger source file"].endswith(".pdf")
    assert january_2024["Passenger PDF page"] == "1"
    assert rows["2010-01"]["Passenger PDF page"] == "HTML page"
    assert rows["2010-01"]["Cargo tons"] == "149,901"
    revised = rows["2025-03"]
    assert "Revised report" in revised["Notes"]
    assert "Revised" in revised["Passenger source file"]
    assert rows["2010-07"]["Passenger movements"] == "Gap (no value)"
    assert rows["2013-06"]["Cargo tons"] == "Held (no value)"
    assert "CYTD step differs" in rows["2013-06"]["Notes"]


def test_year_selector_and_measure_update_the_comparison_table():
    result = app()
    tab = traffic(result)
    assert tab.selectbox(key="traffic_year").value == 2025
    tab.selectbox(key="traffic_year").set_value(2019).run()
    assert not result.exception
    comparison = traffic(result).dataframe[0].value
    assert list(comparison.columns) == ["Month", "2018", "2019", "Change", "Change (%)"]
    assert len(comparison) == 12
    traffic(result).radio(key="traffic_measure").set_value("Cargo tons").run()
    assert not result.exception
    comparison = traffic(result).dataframe[0].value
    series = traffic_view.load_traffic_series()
    assert comparison.iloc[0]["2018"] == f"{series.by_period()['2018-01'].cargo_tons.value:,}" == "196,352"
    assert comparison.iloc[0]["2019"] == f"{series.by_period()['2019-01'].cargo_tons.value:,}"


def test_traffic_tab_error_state_is_safe_and_scoped(monkeypatch):
    def failed_input(data_dir=traffic_view.DATA_DIR):
        raise OSError("Could not read /private/synthetic-operator/traffic.json")

    st.cache_resource.clear()
    monkeypatch.setattr(traffic_view, "load_traffic_series", failed_input)
    try:
        result = AppTest.from_file(APP, default_timeout=30).run()
        assert not result.exception
        tab = traffic(result)
        assert len(tab.error) == 1
        assert "could not be validated" in tab.error[0].value
        assert len(tab.get("plotly_chart")) == 0
        assert "/private/" not in tab_text(tab)
    finally:
        st.cache_resource.clear()
