"""Streamlit's simulated runtime checks the read-only Traffic section."""

import json
import re
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

from mia_capital_intelligence import traffic_view

APP = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def app():
    result = AppTest.from_file(APP, default_timeout=30).run()
    assert not result.exception
    return result


def traffic(result):
    """Open the Traffic section; it is the only section rendered, so the page is the section."""
    result.radio(key="section").set_value("Traffic").run()
    assert not result.exception
    return result


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


def test_traffic_section_renders_its_sections_in_order():
    result = traffic(app())
    assert result.header[0].value == "Monthly airport traffic"
    assert [item.value for item in result.subheader] == [
        "Monthly passenger movements, 2010 to 2026", "Year-on-year comparison", "Exact values and sources",
    ]
    assert len(result.get("plotly_chart")) == 2
    assert not result.error


def test_traffic_copy_is_plain_statements_without_questions():
    tab = traffic(app())
    text = tab_text(tab)
    assert "?" not in text
    assert not re.search(r"\bwhat is\b|\bwhy\b|\bhow\b", text, re.IGNORECASE)
    assert "Monthly passenger movements, 2010 to 2026" in text
    assert "Monthly total cargo tons" in text or "monthly total cargo tons" in text


def test_about_these_figures_is_the_last_element_before_the_site_footer():
    tab = traffic(app())
    children = list(tab.main.children.values())
    footer = children[-2:]
    assert [type(child).__name__ for child in footer] == ["Divider", "Caption"]
    last = children[-3]
    assert last.type == "expander" and last.label == "About these figures"
    assert any(child is last for child in children[:-3]) is False


def test_about_these_figures_states_the_plain_facts():
    tab = traffic(app())
    note = next(item for item in tab.expander if item.label == "About these figures")
    copy = "\n".join(element.value for element in note.markdown)
    assert "Miami International Airport" in copy
    assert "**2010-07** (July 2010) has no source page" in copy
    assert "**2013-06** (June 2013) is held" in copy
    assert "**March 2025** comes from a revised report" in copy
    assert "**March 2020 to December 2021** is the pandemic period" in copy
    assert "199 reported months" in copy
    assert "PDF page numbers count from 1" in copy
    assert "?" not in copy and "Why" not in copy and "What is" not in copy


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
    result = traffic(app())
    assert result.radio(key="traffic_year").value == 2025
    result.radio(key="traffic_year").set_value(2019).run()
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


def test_traffic_error_state_is_safe_and_scoped(monkeypatch):
    def failed_input(data_dir=traffic_view.DATA_DIR):
        raise OSError("Could not read /private/synthetic-operator/traffic.json")

    st.cache_resource.clear()
    monkeypatch.setattr(traffic_view, "load_traffic_series", failed_input)
    try:
        result = AppTest.from_file(APP, default_timeout=30).run()
        assert not result.exception
        assert len(result.error) == 1
        assert "could not be validated" in result.error[0].value
        result = traffic(result)
        assert len(result.error) == 1
        assert "could not be validated" in result.error[0].value
        assert len(result.get("plotly_chart")) == 0
        assert "/private/" not in tab_text(result)
    finally:
        st.cache_resource.clear()
