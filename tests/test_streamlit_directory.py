"""Streamlit's simulated runtime checks the overview-first public directory and its evidence flows."""

from html import escape
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit

from streamlit.testing.v1 import AppTest

from mia_capital_intelligence.app_tabs.app_common import CLOSED_SPENDING_MESSAGES
from mia_capital_intelligence.app_tabs.explore import markdown_label
from mia_capital_intelligence.directory_queries import (
    ESTIMATE_BANDS, DirectoryFilters, format_usd, search_records,
)
from mia_capital_intelligence.estimate_insights import range_records
from mia_capital_intelligence.operations_updates import OPERATING_AREAS
from mia_capital_intelligence.public_registry import load_registry

APP = Path(__file__).resolve().parents[1] / "streamlit_app.py"
SECTION_LABELS = ("Overview", "Projects", "Traffic", "Spending", "Sources & Coverage")


def app():
    result = AppTest.from_file(APP, default_timeout=15).run()
    assert not result.exception
    return result


def go(result, section):
    result.radio(key="section").set_value(section).run()
    assert not result.exception
    assert result.radio(key="section").value == section
    return result


def visible_copy(result):
    return "\n".join(
        str(element.value) for kind in ("markdown", "caption", "subheader", "info", "warning")
        for element in result.get(kind)
    )


def overview_search(result, term):
    result.text_input(key="overview_search").input(term)
    return result.button(key="FormSubmitter:overview-search-Search").click().run()


def record_buttons(result):
    return [button for button in result.button if (button.key or "").startswith("record-")]


def tiles(result):
    return [button for button in result.button if (button.key or "").startswith("area-tile-")]


def open_buttons(result):
    return [button for button in result.button if (button.key or "").startswith("open-") and ":" in button.key]


def drilldown_open(result):
    return any(button.key == "overview-range-back" for button in result.button)


def record_links(result):
    """(label, url) pairs from the one-line caption of a record card or record page."""
    return [pair for item in result.caption for pair in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", item.value)]


def link_rows(result, prefix):
    """URLs of link buttons and one-line caption links whose label starts with prefix."""
    buttons = [row.proto.url for row in result.get("link_button") if row.proto.label.startswith(prefix)]
    captions = [url for label, url in record_links(result) if label.startswith(prefix)]
    return buttons + captions


def advanced_estimates(result):
    return next(item for item in result.expander if item.label == "Estimate ranges and interactive ranking")


def test_overview_is_the_first_section_and_sections_are_click_selected():
    result = app()
    assert result.radio(key="section").value == "Overview"
    assert list(result.radio(key="section").options) == list(SECTION_LABELS)
    assert not result.tabs and not record_buttons(result)
    copy = visible_copy(result)
    assert "Explore airport improvements and reported project costs." in copy
    assert "Operations updates from the county's quarterly report, grouped by area." in copy
    assert "No affiliation with MDAD or HNTB" not in copy
    assert "Service areas" in [item.value for item in result.subheader]


def test_service_areas_show_one_tile_per_area_with_update_counts():
    result = app()
    labels = [button.label for button in tiles(result)]
    assert len(labels) == len(OPERATING_AREAS) == 4
    for area, count in (
        ("Gates & connections", "2 project updates"), ("Security screening", "1 project update"),
        ("Baggage systems", "1 project update"), ("Runways & taxiways", "1 project update"),
    ):
        assert any(area in label and count in label for label in labels), area


def test_overview_panels_show_estimates_spending_gate_and_latest_traffic():
    result = app()
    html = [item.proto.body for item in result.get("html") if "mia-estimate-bands" in item.proto.body]
    assert len(html) == 1
    assert re.search(r'<span class="mia-band-name">\$100M or more</span><span class="mia-band-count">16</span>', html[0])
    assert "<a " not in html[0]
    assert "Select a range to list its records." in visible_copy(result)
    spending_text = [item.value for item in result.info] + [item.value for item in result.warning]
    closed = [text for text in spending_text if text in CLOSED_SPENDING_MESSAGES.values()]
    if closed:
        assert len(closed) == 1
        assert not any("Reported through September" in frame.value.to_string() for frame in result.dataframe)
    else:
        assert any("Reported through September" in frame.value.to_string() for frame in result.dataframe)
    labels = [metric.label for metric in result.metric]
    assert any(label.startswith("Passenger movements, ") for label in labels)
    assert any(label.startswith("Total cargo tons, ") for label in labels)
    assert any(button.label == "See the Traffic section" for button in result.button)



def test_only_the_overview_search_box_accepts_free_text_and_no_dropdowns_appear():
    result = app()
    for section in SECTION_LABELS:
        go(result, section)
        keys = [item.key for item in result.text_input]
        assert keys == (["overview_search"] if section == "Overview" else []), section
        assert len(result.selectbox) == 0, section



def test_overview_search_lists_matching_projects_on_the_overview():
    registry = load_registry()
    expected = len(search_records(registry, DirectoryFilters("CA176A")))
    result = overview_search(app(), "CA176A")
    assert not result.exception
    assert result.radio(key="section").value == "Overview"
    assert f"{expected} matching source record" in visible_copy(result)
    assert len(link_rows(result, "Link to this record")) == expected
    assert not record_buttons(result)



def test_report_search_opens_the_source_document():
    result = overview_search(app(), "261402")
    report = next(button for button in result.button if button.key == "report-261402")
    report.click().run()
    assert not result.exception
    assert result.radio(key="section").value == "Sources & Coverage"
    assert result.radio(key="coverage_source").value == "261402"



def test_service_tile_shows_its_projects_on_the_overview():
    result = app()
    tiles(result)[0].click().run()
    assert not result.exception
    assert result.radio(key="section").value == "Overview"
    assert "Gates & connections" in [row.value for row in result.subheader]
    assert len(open_buttons(result)) == 2
    assert not record_buttons(result)



def test_projects_opens_the_latest_report_without_a_search_step():
    result = go(app(), "Projects")
    assert not result.exception
    assert result.radio(key="source_report").value == "261824"
    assert "110 matching source records" in visible_copy(result)
    assert len(record_buttons(result)) == 5
    assert not result.text_input


def test_overview_caption_credits_miami_dade_county_for_memo():
    result = app()
    captions = [item.value for item in result.caption if "Memo dated" in item.value]
    assert len(captions) == 1
    assert captions[0].startswith("Miami-Dade County · ")
    assert "Miami International Airport" not in captions[0]



def test_security_tile_preserves_versioned_project_and_memo_links():
    result = app()
    tiles(result)[1].click().run()
    assert not result.exception
    assert result.radio(key="section").value == "Overview"
    assert "Security screening" in [row.value for row in result.subheader]
    assert "upgrade one checkpoint at a time" in visible_copy(result)
    assert "See how MIA is upgrading" not in visible_copy(result)
    cards = open_buttons(result)
    expected = next(row.source_ref for row in load_registry().records
                    if row.matter_id == "261402" and row.project_id == "BA013A")
    assert [card.key for card in cards] == [f"open-{expected}"]
    memo = next(item.value for item in result.markdown if item.value.startswith("[Read report update]"))
    assert re.findall(r"\]\(([^)]+)\)", memo)[0].endswith("/261402.pdf#page=6")



def test_overview_search_rows_link_to_the_official_page_and_record():
    registry = load_registry()
    reference = next(row.source_ref for row in registry.records
                     if row.project_id == "CA176A" and row.matter_id == "261402")
    result = overview_search(app(), "CA176A")
    assert not result.exception
    assert any(url.endswith("/261402.pdf#page=12") for url in link_rows(result, "Open official PDF"))
    assert any(parse_qs(urlsplit(url).query)["record"] == [reference]
               for url in link_rows(result, "Link to this record"))
    row_html = "".join(item.proto.body for item in result.get("html") if "MIA E Satellite" in item.proto.body)
    assert "Reported estimate" in row_html and "$ 3,191,832" in row_html

    linked = AppTest.from_file(APP, default_timeout=15)
    linked.query_params["record"] = reference
    linked.run()
    assert not linked.exception
    assert linked.metric[0].value == "$ 3,191,832"
    assert any("MIA E Satellite Terminal Seating Ph2" == row.value for row in linked.subheader)
    matter = next(row for row in registry.catalog if row["matter_id"] == "261402")
    assert any(matter["sha256"] in item.proto.body for item in linked.get("html"))
    assert any(url.endswith("/261402.pdf#page=12") for label, url in record_links(linked)
               if label.startswith("Open official PDF"))
    copy = visible_copy(linked)
    assert "Same ID in another report" in "\n".join(row.label for row in linked.expander)
    evidence = next(item for item in linked.expander if item.label == "Report and source details")
    assert "Original project description" in visible_copy(evidence)
    assert "cost_growth" not in copy and "cost overrun" not in copy



def test_project_brief_shows_sourced_roles_and_hides_missing_roles_on_selection():
    registry = load_registry()
    for project, name, company, contract_id, matter_id in (
        ("U010D-I", "Ricardo Lopez", "Magnum Construction Management, LLC", "U010D-1", "252233"),
        ("X078A", "Joachim Perez", "Lemartec-NV2A JV, LLC", "DB23AV01", "250831"),
    ):
        reference = next(row.source_ref for row in registry.records
                         if row.matter_id == "261402" and row.project_id == project)
        result = AppTest.from_file(APP, default_timeout=15)
        result.query_params["record"] = reference
        result.run()
        assert not result.exception
        brief = next(item for item in result.expander if item.label == "Project brief and delivery team")
        copy = visible_copy(brief)
        assert f"Project lead** · {name}" in copy
        assert f"Awarded contractor** · {company}" in copy
        assert contract_id in copy
        assert f"/Y2025/{matter_id}.pdf#page=5" in copy
        assert f"matter={matter_id}&yearFolder=Y2025" in copy

    reference = next(row.source_ref for row in registry.records
                     if row.matter_id == "261402" and row.project_id == "V008B")
    result = AppTest.from_file(APP, default_timeout=15)
    result.query_params["record"] = reference
    result.run()
    assert not result.exception
    brief = next(item for item in result.expander if item.label == "Project brief")
    assert "gates F4, F6 and F8" in brief.get("html")[0].proto.body
    copy = visible_copy(brief)
    assert "Reporting agency** · Miami-Dade Aviation Department" in copy
    assert "Project lead" not in copy
    assert "Awarded contractor" not in copy


def test_airport_and_report_filters_work_in_the_projects_list():
    result = go(app(), "Projects")
    result.radio(key="airport").set_value("TMB").run()
    assert not result.exception
    assert len(record_buttons(result)) == 3
    assert all("Miami Executive Airport · Apr–Jun 2026" in row.label for row in record_buttons(result))
    result.toggle(key="explore_table").set_value(True).run()
    assert not result.exception
    assert result.dataframe[0].value.shape[0] == 3
    assert set(result.dataframe[0].value["Airport"]) == {"TMB"}
    result.radio(key="source_report").set_value("all").run()
    assert result.dataframe[0].value.shape[0] == 9



def test_all_reports_preserves_distinct_source_links_across_result_views():
    registry = load_registry()
    result = overview_search(app(), "X078A")
    assert not result.exception
    official = link_rows(result, "Open official PDF")
    assert len(official) == 3
    assert any(url.endswith("/261824.pdf#page=16") for url in official)
    assert any(url.endswith("/261402.pdf#page=13") for url in official)
    assert any(url.endswith("/260526.pdf#page=12") for url in official)
    permalinks = {parse_qs(urlsplit(url).query)["record"][0] for url in link_rows(result, "Link to this record")}
    assert permalinks == {row.source_ref for row in registry.records
                          if row.project_id == "X078A" and row.matter_id in {"261824", "261402", "260526"}}


def test_unknown_airport_records_and_missing_fields_remain_visible():
    result = go(app(), "Projects")
    result.radio(key="source_report").set_value("all").run()
    result.radio(key="airport").set_value("Unknown").run()
    record_buttons(result)[0].click().run()
    result.toggle(key="explore_table").set_value(True).run()
    assert not result.exception
    assert result.dataframe[0].value.shape[0] == 23
    assert set(result.dataframe[0].value["Airport"]) == {"Unknown"}
    assert "The description does not identify a single airport." in visible_copy(result)



def test_empty_search_has_meaningful_message_and_keeps_source_catalog():
    result = overview_search(app(), "not-a-real-project-xyz")
    assert not result.exception
    assert not link_rows(result, "Link to this record")
    assert "No source records match this search" in visible_copy(result)
    go(result, "Sources & Coverage")
    assert result.dataframe[0].value.shape[0] == 4


def test_cataloged_only_report_does_not_claim_full_indexing():
    result = go(app(), "Sources & Coverage")
    result.radio(key="coverage_source").set_value("261400").run()
    assert not result.exception
    copy = visible_copy(result)
    assert "Contract spending**  Exhibit B, PDF page 30" in copy
    assert result.dataframe[0].value["Source records"].tolist() == [110, 112, 0, 110]


def test_versioned_record_deep_link_opens_individual_observation():
    registry = load_registry()
    source_ref = next(row.source_ref for row in registry.records
                      if row.project_id == "CA176A" and row.matter_id == "260526")
    linked = AppTest.from_file(APP, default_timeout=15)
    linked.query_params["record"] = source_ref
    linked.run()
    assert not linked.exception
    assert not linked.text_input and not linked.tabs
    links = record_links(linked)
    permalink = next(url for label, url in links if label == "Link to this record")
    assert parse_qs(urlsplit(permalink).query)["record"] == [source_ref]
    assert any(url.endswith("/260526.pdf#page=11") for label, url in links)


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
    result = go(app(), "Projects")
    assert len(advanced_estimates(result).get("plotly_chart")) == 1
    assert "Showing the 10 largest of 110 records." in visible_copy(result)
    result.radio(key="chart_airport").set_value("TMB").run()
    assert not result.exception
    assert "Showing the 3 largest of 3 records." in visible_copy(result)
    selector = next(row for row in result.radio if row.label == "Explore a chart record")
    from mia_capital_intelligence.estimate_insights import largest_estimates
    reference = largest_estimates(load_registry(), "261824", "TMB").rows[-1]["source_ref"]
    selector.set_value(reference).run()
    assert next(row for row in result.radio if row.label == "Explore a chart record").value == reference
    assert not result.exception
    assert advanced_estimates(result).metric[0].value
    result.radio(key="chart_report").set_value("260526").run()
    assert "Showing the 3 largest of 3 records. 0 records have no reported estimate." in visible_copy(result)
    assert not any(item.key == "chart_search" for item in result.text_input)


def test_chart_event_resolves_to_detail_and_selection_can_override(monkeypatch):
    import streamlit as st
    registry = load_registry()
    reference = next(row.source_ref for row in registry.records
                     if row.matter_id == "261824" and row.project_id == "V008B")
    monkeypatch.setattr(st, "plotly_chart", lambda *a, **kw: {"selection":{"points":[{"customdata":[reference]}]}})
    result = go(app(), "Projects")
    selector = next(row for row in result.radio if row.label == "Explore a chart record")
    assert selector.value == reference
    from mia_capital_intelligence.estimate_insights import largest_estimates
    other = largest_estimates(registry, "261824").rows[0]["source_ref"]
    selector.set_value(other).run()
    assert not result.exception
    assert next(row for row in result.radio if row.label == "Explore a chart record").value == other



def test_chart_permalink_is_independent_of_directory_search(monkeypatch):
    import streamlit as st

    registry = load_registry()
    reference = next(row.source_ref for row in registry.records
                     if row.matter_id == "261824" and row.project_id == "V008B")
    result = go(app(), "Projects")
    button = record_buttons(result)[0]
    directory_ref = button.key.removeprefix("record-")
    button.click().run()
    monkeypatch.setattr(st, "plotly_chart", lambda *args, **kwargs: {
        "selection": {"points": [{"customdata": [reference]}]},
    })
    result.run()
    assert not result.exception and not result.query_params.get("record")
    explore_links = [url for label, url in record_links(result) if label == "Link to this record"]
    assert [parse_qs(urlsplit(url).query)["record"][0] for url in explore_links] == [directory_ref, reference]

    linked = AppTest.from_file(APP, default_timeout=15)
    linked.query_params["record"] = reference
    linked.run()
    assert not linked.exception and not linked.tabs
    assert linked.metric[0].value == "$ 896,021,864"
    assert any(url.endswith("/261824.pdf#page=16") for label, url in record_links(linked))


def test_projects_deep_link_opens_same_report_directory_and_pair():
    # The Overview bars are no longer links; this query route stays valid for shared links.
    params = {"report": ["261402"], "range": ["$100M or more"]}

    linked = AppTest.from_file(APP, default_timeout=15)
    for name, values in params.items():
        linked.query_params[name] = values[0]
    linked.run()
    assert not linked.exception
    assert linked.radio(key="section").value == "Projects"
    linked.toggle(key="explore_table").set_value(True).run()
    assert linked.dataframe[0].value.shape[0] == 16
    selection = next(group for group in linked.button_group if (group.key or "").startswith("same-report-pair-"))
    rows = load_registry().records
    pair = [row.source_ref for row in rows if row.matter_id == "261402" and row.project_id in {"T180B", "V008B"}]
    selection.set_value(pair).run()
    assert not linked.exception
    assert {"$ 1,066,231,593", "$ 896,021,864"} <= {metric.value for metric in linked.metric}
    assert all(ref.startswith("261402:") for ref in next(
        group for group in linked.button_group if (group.key or "").startswith("same-report-pair-")).value)

    linked.radio(key="source_report").set_value("all").run()
    assert not linked.exception
    assert not any((group.key or "").startswith("same-report-pair-") for group in linked.button_group)


def estimate_html(result):
    return next(item.proto.body for item in result.get("html") if "mia-estimate-bands" in item.proto.body)


def drilldown_html(result):
    return "".join(item.proto.body for item in result.get("html") if "mia-drill-name" in item.proto.body)



def test_overview_range_click_opens_a_sub_dashboard_with_count_total_and_original_files():
    registry = load_registry()
    result = app()
    assert not drilldown_open(result)
    result.radio(key="overview_range").set_value("$100M or more").run()
    assert not result.exception
    assert result.radio(key="section").value == "Overview"
    assert not record_buttons(result)
    rows = range_records(registry, "261824", "$100M or more")
    assert len(rows) == 16
    assert markdown_label("$100M or more") in [row.value for row in result.subheader]
    metrics = {metric.label: metric.value for metric in result.metric}
    assert metrics["Records in this range"] == "16"
    assert metrics["Total reported estimate · USD"] == format_usd(sum(row["estimate_usd"] for row in rows))
    official = link_rows(result, "Open official PDF")
    permalinks = link_rows(result, "Link to this record")
    assert len(official) == len(permalinks) == 16
    for row, url in zip(rows, official, strict=True):
        assert url.endswith(f"/261824.pdf#page={row['pdf_page']}")
    for row, url in zip(rows, permalinks, strict=True):
        assert parse_qs(urlsplit(url).query)["record"] == [row["source_ref"]]
    listed = drilldown_html(result)
    for row in rows:
        assert escape(row["project_name"]) in listed
    assert listed.count("Reported estimate") == 16


def test_all_range_lists_every_record_with_a_known_estimate():
    registry = load_registry()
    result = app()
    result.radio(key="overview_range").set_value("All").run()
    assert not result.exception
    rows = range_records(registry, "261824")
    metrics = {metric.label: metric.value for metric in result.metric}
    assert metrics["Records in this range"] == f"{len(rows):,}"
    assert len(link_rows(result, "Link to this record")) == len(rows)


def test_back_to_overview_closes_the_range_sub_dashboard_without_leaving_overview():
    result = app()
    result.radio(key="overview_range").set_value("Under $10M").run()
    assert drilldown_open(result)
    result.button(key="overview-range-back").click().run()
    assert not result.exception
    assert result.radio(key="section").value == "Overview"
    assert result.radio(key="overview_range").value is None
    assert not drilldown_open(result)
    assert not link_rows(result, "Open official PDF")



def test_range_bars_are_not_links_and_the_list_links_only_after_a_choice():
    result = app()
    assert "<a " not in estimate_html(result) and "href=" not in estimate_html(result)
    for band in ESTIMATE_BANDS:
        assert band in estimate_html(result)
    assert not link_rows(result, "Open official PDF")
    assert not any("$" in button.label for button in result.button)
    result.radio(key="overview_range").set_value("Under $10M").run()
    assert "<a " not in estimate_html(result)
    assert link_rows(result, "Open official PDF")


def test_projects_range_labels_use_one_format_for_every_band():
    result = go(app(), "Projects")
    assert not result.exception
    labels = list(result.radio(key="estimate_range").options)[1:]
    assert labels == [markdown_label(band) for band in ESTIMATE_BANDS]
    assert all(label.count("\\$") == band.count("$") for label, band in zip(labels, ESTIMATE_BANDS, strict=True))


def test_t180b_case_surfaces_published_amounts_and_sources():
    coverage = go(app(), "Sources & Coverage")
    assert "earlier report separately lists T180D" in visible_copy(coverage)
    assert {"$ 914,627,764", "$ 1,066,231,593"} <= {metric.value for metric in coverage.metric}
    links = {row.proto.url for row in coverage.get("link_button")} | {url for _, url in record_links(coverage)}
    assert any(link.endswith("/260526.pdf#page=11") for link in links)
    assert any(link.endswith("/261402.pdf#page=12") for link in links)
    assert "$ 151,603,829" not in visible_copy(coverage)



def test_empty_search_state_renders():
    result = overview_search(app(), "not-a-real-project-xyz")
    assert not result.exception
    assert "No source records match this search" in visible_copy(result)


def test_valid_record_permalink_renders():
    source_ref = next(row.source_ref for row in load_registry().records
                      if row.project_id == "CA176A" and row.matter_id == "260526")
    linked = AppTest.from_file(APP, default_timeout=15)
    linked.query_params["record"] = source_ref
    linked.run()
    assert not linked.exception
    assert any(label == "Link to this record" for label, _ in record_links(linked))


def test_invalid_record_link_renders():
    result = AppTest.from_file(APP, default_timeout=15)
    result.query_params["record"] = "stale-source-version"
    result.run()
    assert not result.exception
    assert "outside the current registry version" in visible_copy(result)


def test_registry_error_state_renders(monkeypatch):
    import streamlit as st
    from mia_capital_intelligence import public_registry

    def failed_input(root):
        raise OSError("Could not read /private/synthetic-operator/registry.json")

    st.cache_resource.clear()
    monkeypatch.setattr(public_registry, "load_registry", failed_input)
    try:
        result = AppTest.from_file(APP, default_timeout=15).run()
        assert not result.exception
        assert "could not be validated" in result.error[0].value
    finally:
        st.cache_resource.clear()


def test_sections_run_in_the_approved_order_with_the_capital_c_coverage_label():
    result = app()
    assert list(result.radio(key="section").options) == [
        "Overview", "Projects", "Traffic", "Spending", "Sources & Coverage",
    ]
    assert "Sources & coverage" not in list(result.radio(key="section").options)


def test_projects_has_no_text_input_or_service_area_control():
    result = go(app(), "Projects")
    assert not result.exception
    assert not result.text_input
    assert not any(row.key == "area" or row.label == "Service area" for row in result.radio)
    assert not any((button.key or "").startswith("FormSubmitter:explore-search") for button in result.button)
    assert "Report period" in [row.label for row in result.radio]
    assert "Search for a project or report" not in visible_copy(result)
