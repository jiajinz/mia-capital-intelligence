"""Streamlit's simulated runtime checks the directory-to-evidence user flow."""

from pathlib import Path

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
    assert "No affiliation with MDAD or HNTB" in copy
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
    assert result.dataframe[0].value.shape[0] == 3
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
    assert len(result.metric) == 0
    assert "No source records match these filters" in visible_copy(result)
    assert result.dataframe[0].value.shape[0] == 3


def test_cataloged_only_report_does_not_claim_full_indexing():
    result = app()
    result.selectbox(key="coverage_source").set_value("261400").run()
    assert not result.exception
    copy = visible_copy(result)
    assert "Cataloged only" in copy
    assert "No project records from this report are indexed" in copy
    assert "first public posting date" in copy
    assert result.dataframe[1].value["Indexed records"].tolist() == [110, 112, 0]


def test_versioned_record_deep_link_opens_individual_observation():
    registry = load_registry()
    source_ref = next(row.source_ref for row in registry.records
                      if row.project_id == "CA176A" and row.matter_id == "260526")
    linked = AppTest.from_file(APP, default_timeout=15)
    linked.query_params["record"] = source_ref
    linked.run()
    assert not linked.exception
    assert linked.selectbox(key="selected_record").value == source_ref
    assert any(row.proto.url.endswith("/260526.pdf#page=11") for row in linked.get("link_button"))


def test_invalid_record_link_has_an_explicit_version_warning():
    result = AppTest.from_file(APP, default_timeout=15)
    result.query_params["record"] = "stale-source-version"
    result.run()
    assert not result.exception
    assert "outside the current registry version" in visible_copy(result)
    assert result.metric[0].value


def test_invalid_published_input_has_a_safe_error_state(monkeypatch):
    import streamlit as st
    from mia_capital_intelligence import public_registry

    def failed_input(root):
        raise ValueError("Synthetic corrupt public input")

    st.cache_resource.clear()
    monkeypatch.setattr(public_registry, "load_registry", failed_input)
    try:
        result = AppTest.from_file(APP, default_timeout=15).run()
        assert not result.exception
        assert len(result.error) == 1
        assert "could not be validated" in result.error[0].value
        assert len(result.metric) == 0 and len(result.dataframe) == 0
    finally:
        st.cache_resource.clear()
