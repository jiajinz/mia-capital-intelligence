"""Streamlit's simulated runtime checks the directory-to-evidence user flow."""

from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from streamlit.testing.v1 import AppTest

from mia_capital_intelligence.public_registry import load_registry

APP = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def app():
    result = AppTest.from_file(APP, default_timeout=15).run()
    assert not result.exception
    return result


def visible_copy(result):
    return "\n".join(
        str(element.value) for kind in ("markdown", "caption", "subheader", "info", "warning")
        for element in result.get(kind)
    )


def test_directory_renders_controlled_records_and_public_context():
    result = app()
    assert result.dataframe[0].value.shape[0] == 222
    copy = visible_copy(result)
    assert "222 source records" in copy
    assert "Airport Infrastructure & Capital Projects Explorer" in copy
    assert "No affiliation with MDAD or HNTB" not in copy
    assert "Project directory" in copy
    assert "cross-report identities remain unresolved" in copy


def test_real_search_to_detail_preserves_estimate_and_official_page():
    result = app()
    result.text_input(key="search").input("CA176A").run()
    assert not result.exception
    assert result.dataframe[0].value.shape[0] == 2
    assert result.metric[0].value == "$ 3,191,832"
    assert any("MIA E Satellite Terminal Seating Ph2" == row.value for row in result.subheader)
    links = result.get("link_button")
    assert any(row.proto.url.endswith("/261402.pdf#page=12") for row in links)
    copy = visible_copy(result)
    assert "Same ID in another report" in "\n".join(row.label for row in result.expander)
    assert "original source-row text" in copy.lower() or "original source-row" in copy.lower() or "original project description" in copy.lower()
    assert "cost_growth" not in copy and "cost overrun" not in copy


def test_airport_and_source_filters_work():
    result = app()
    result.selectbox(key="airport").set_value("TMB").run()
    assert not result.exception
    assert result.dataframe[0].value.shape[0] == 6
    assert set(result.dataframe[0].value["Airport"]) == {"TMB"}
    result.selectbox(key="source_report").set_value("261402").run()
    assert not result.exception
    assert result.tabs[0].dataframe[0].value.shape[0] == 3
    assert result.selectbox(key="selected_record").value.startswith("261402:")


def test_unknown_airport_records_and_missing_fields_remain_visible():
    result = app()
    result.selectbox(key="airport").set_value("Unknown").run()
    assert not result.exception
    assert result.dataframe[0].value.shape[0] == 15
    assert set(result.dataframe[0].value["Airport"]) == {"Unknown"}
    assert "status and milestones are not indexed" in visible_copy(result)


def test_empty_search_has_meaningful_message_and_keeps_source_catalog():
    result = app()
    result.text_input(key="search").input("not-a-real-project-xyz").run()
    assert not result.exception
    assert len(result.tabs[0].metric) == 0
    assert "No source records match these filters" in visible_copy(result)
    assert result.tabs[2].dataframe[0].value.shape[0] == 3


def test_cataloged_only_report_does_not_claim_full_indexing():
    result = app()
    result.selectbox(key="coverage_source").set_value("261400").run()
    assert not result.exception
    copy = visible_copy(result)
    assert "Cataloged only" in copy
    assert "No project records from this report are indexed" in copy
    assert "first public posting date" in copy
    assert result.tabs[2].dataframe[0].value["Indexed records"].tolist() == [110, 112, 0]


def test_versioned_record_deep_link_opens_individual_observation():
    registry = load_registry()
    source_ref = next(row.source_ref for row in registry.records
                      if row.project_id == "CA176A" and row.matter_id == "260526")
    linked = AppTest.from_file(APP, default_timeout=15)
    linked.query_params["record"] = source_ref
    linked.run()
    assert not linked.exception
    assert not linked.text_input and not linked.tabs
    assert any(row.value == source_ref for row in linked.code)
    assert any(row.proto.url.endswith("/260526.pdf#page=11") for row in linked.get("link_button"))


def test_invalid_record_link_has_an_explicit_version_warning():
    result = AppTest.from_file(APP, default_timeout=15)
    result.query_params["record"] = "stale-source-version"
    result.run()
    assert not result.exception
    assert "outside the current registry version" in visible_copy(result)
    assert not result.metric
    assert any(row.proto.label == "Browse project records" for row in result.get("link_button"))


def test_invalid_published_input_has_a_safe_error_state(monkeypatch):
    import streamlit as st
    from mia_capital_intelligence import public_registry

    def failed_input(root):
        raise OSError("Could not read /private/synthetic-operator/registry.json")

    st.cache_resource.clear()
    monkeypatch.setattr(public_registry, "load_registry", failed_input)
    try:
        result = AppTest.from_file(APP, default_timeout=15).run()
        assert not result.exception
        assert len(result.error) == 1
        assert "could not be validated" in result.error[0].value
        assert not result.text
        assert len(result.metric) == 0 and len(result.dataframe) == 0
    finally:
        st.cache_resource.clear()


def test_chart_filters_and_accessible_selection_open_original_record():
    result = app()
    assert len(result.tabs[1].get("plotly_chart")) == 1
    assert "10 largest of 112 matching" in visible_copy(result)
    result.selectbox(key="chart_airport").set_value("TMB").run()
    assert not result.exception
    assert "3 largest of 3 matching" in visible_copy(result)
    selector = next(row for row in result.selectbox if row.label == "Explore a chart record")
    from mia_capital_intelligence.estimate_insights import largest_estimates
    reference = largest_estimates(load_registry(), "261402", "TMB").rows[-1]["source_ref"]
    selector.set_value(reference).run()
    assert next(row for row in result.selectbox if row.label == "Explore a chart record").value == reference
    assert not result.exception
    assert result.tabs[1].metric[0].value
    result.selectbox(key="chart_report").set_value("260526").run()
    assert "110 indexed rows" in visible_copy(result)
    result.text_input(key="chart_search").input("not-a-real-project").run()
    assert not result.exception
    assert not result.tabs[1].get("plotly_chart")
    assert "No known cost estimates" in visible_copy(result)


def test_chart_event_resolves_to_detail_and_dropdown_can_override(monkeypatch):
    import streamlit as st
    registry = load_registry()
    reference = next(row.source_ref for row in registry.records
                     if row.matter_id == "261402" and row.project_id == "V008B")
    monkeypatch.setattr(st, "plotly_chart", lambda *a, **kw: {"selection":{"points":[{"customdata":[reference]}]}})
    result = app()
    selector = next(row for row in result.selectbox if row.label == "Explore a chart record")
    assert selector.value == reference
    from mia_capital_intelligence.estimate_insights import largest_estimates
    other = largest_estimates(registry,"261402").rows[0]["source_ref"]
    selector.set_value(other).run()
    assert not result.exception
    assert next(row for row in result.selectbox if row.label == "Explore a chart record").value == other


def test_chart_permalink_is_independent_of_directory_search(monkeypatch):
    import streamlit as st

    registry = load_registry()
    reference = next(row.source_ref for row in registry.records
                     if row.matter_id == "261402" and row.project_id == "V008B")
    result = app()
    result.text_input(key="search").input("CA176A").run()
    directory_ref = result.selectbox(key="selected_record").value
    monkeypatch.setattr(st, "plotly_chart", lambda *args, **kwargs: {
        "selection": {"points": [{"customdata": [reference]}]},
    })
    result.run()
    assert not result.exception and not result.query_params.get("record")
    for tab, expected in zip(result.tabs[:2], (directory_ref, reference), strict=True):
        link = next(row for row in tab.get("link_button") if row.proto.label == "Open profile permalink")
        assert parse_qs(urlsplit(link.proto.url).query) == {"record": [expected]}

    linked = AppTest.from_file(APP, default_timeout=15)
    linked.query_params["record"] = reference
    linked.run()
    assert not linked.exception and not linked.tabs
    assert linked.metric[0].value == "$ 896,021,864"
    assert any(row.proto.url.endswith("/261402.pdf#page=13") for row in linked.get("link_button"))
