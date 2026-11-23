"""Protect the chart's population, exact ranking and evidence navigation."""
from dataclasses import replace
from decimal import Decimal

import pytest

from mia_capital_intelligence.directory_queries import format_usd
from mia_capital_intelligence.estimate_insights import (
    CHART_LABEL_MAX_CHARS, CHART_NAMES, ESTIMATE_AXIS_TITLE, chart_label, chart_labels, estimate_figure,
    largest_estimates, selected_source_ref,
)
from mia_capital_intelligence.public_registry import METRIC, load_registry


@pytest.fixture
def registry():
    return load_registry()


def test_ranking_is_one_snapshot_not_a_combined_project_population(registry):
    ranking = largest_estimates(registry, '261402')
    assert (ranking.snapshot_count, ranking.matching_count, ranking.missing_count) == (112, 112, 0)
    assert len(ranking.rows) == 10
    assert {row['matter_id'] for row in ranking.rows} == {'261402'}
    assert len({row['source_ref'] for row in ranking.rows}) == 10
    assert ranking.rows[0]['project_id'] == 'T180B'
    assert ranking.rows[0]['estimate_usd'] == Decimal('1066231593')
    assert all(isinstance(row['estimate_usd'], Decimal) for row in ranking.rows)


def test_filters_apply_before_ranking_and_keep_denominators(registry):
    ranking = largest_estimates(registry, '261402', 'TMB', limit=20)
    assert ranking.snapshot_count == 112 and ranking.matching_count == 3
    assert len(ranking.rows) == 3
    assert {row['airport_code'] for row in ranking.rows} == {'TMB'}
    assert len(largest_estimates(registry, '260526').rows) == 10
    assert largest_estimates(registry, '260526').snapshot_count == 110
    assert largest_estimates(registry, '261402', search='not-a-project').matching_count == 0
    assert largest_estimates(registry, '261402', 'Unknown', limit=20).matching_count > 0


@pytest.mark.parametrize('matter,limit', [('261400',10),('missing',10),('261402',0),('261402',21),('261402',True)])
def test_invalid_population_or_limit_is_rejected(registry, matter, limit):
    with pytest.raises(ValueError):
        largest_estimates(registry,matter,limit=limit)


def test_missing_estimate_is_excluded_but_zero_is_rankable(registry):
    records = list(registry.records)
    positions = [i for i,row in enumerate(records) if row.matter_id == '261402']
    for index,value in zip(positions[:2], [None,Decimal('0')]):
        row = records[index]
        records[index] = replace(row, metrics={METRIC: replace(row.metrics[METRIC], value=value)})
    synthetic = replace(registry, records=tuple(records))
    ranking = largest_estimates(synthetic,'261402')
    assert ranking.missing_count == 1 and ranking.matching_count == 112
    zero_id = records[positions[1]].project_id
    assert largest_estimates(synthetic,'261402',search=zero_id).rows[0]['estimate_usd'] == 0


def test_plot_geometry_and_hover_keep_exact_evidence(registry):
    ranking = largest_estimates(registry,'261402')
    figure = estimate_figure(ranking)
    trace = figure.data[0]
    assert trace.orientation == 'h'
    assert trace.customdata[0][0] == ranking.rows[0]['source_ref']
    assert trace.customdata[0][2] == '$ 1,066,231,593'
    assert trace.x[0] == 1066.231593
    assert figure.layout.xaxis.title.text is None  # title is shown below the plot by the app
    assert ESTIMATE_AXIS_TITLE == 'Estimated cost (USD millions)'
    assert 'Estimated cost' in trace.hovertemplate


def test_hover_keeps_full_project_names_even_when_labels_are_truncated(registry):
    ranking = largest_estimates(registry, '261402')
    trace = estimate_figure(ranking).data[0]
    assert [custom[1] for custom in trace.customdata] == [row['project_name'] for row in ranking.rows]
    assert any(len(row['project_name']) > CHART_LABEL_MAX_CHARS for row in ranking.rows)
    assert '%{customdata[1]}' in trace.hovertemplate
    assert list(trace.y) == [row['project_id'] for row in ranking.rows]


def test_displayed_labels_truncate_only_long_names_with_an_ellipsis(registry):
    ranking = largest_estimates(registry, '261402')
    labels = estimate_figure(ranking).layout.yaxis.ticktext
    assert len(labels) == len(ranking.rows)
    assert labels == chart_labels(ranking.rows)
    assert all(len(label) <= CHART_LABEL_MAX_CHARS for label in labels)
    for row, label in zip(ranking.rows, labels):
        full = CHART_NAMES.get(row['project_id'], row['project_name'])
        if ' · ' not in label:  # undisambiguated labels are plain truncations of the full name
            assert label == chart_label(full)
    assert any(label.endswith('…') for label in labels)


def _row(project_id, project_name):
    return {'project_id': project_id, 'project_name': project_name}


def test_identical_truncated_names_get_distinct_ranking_suffixes():
    rows = [
        _row('A1', 'Harbor Expansion Phase One'),
        _row('A2', 'Harbor Expansion Phase Two'),
        _row('A3', 'Gate Upgrade'),
    ]
    assert chart_label(rows[0]['project_name']) == chart_label(rows[1]['project_name'])
    labels = chart_labels(rows)
    assert labels == ('Harbor Expa… · 1', 'Harbor Expa… · 2', 'Gate Upgrade')
    assert len(set(labels)) == len(labels)
    assert all(len(label) <= CHART_LABEL_MAX_CHARS for label in labels)


def test_suffix_keeps_the_ranking_position_across_a_collision_group():
    rows = [
        _row('B1', 'Terminal Redevelopment Alpha'),
        _row('B2', 'Terminal Redevelopment Beta'),
        _row('B3', 'Terminal Redevelopment Gamma'),
    ]
    assert chart_labels(rows) == ('Terminal Re… · 1', 'Terminal Re… · 2', 'Terminal Re… · 3')


def test_ranking_without_collisions_is_unchanged():
    rows = [
        _row('C1', 'Concourse D west extension'),
        _row('C2', 'Short name'),
        _row('C3', 'A considerably longer project name that is truncated'),
    ]
    assert chart_labels(rows) == tuple(chart_label(CHART_NAMES.get(r['project_id'], r['project_name'])) for r in rows)
    assert chart_labels(rows) == ('Concourse D wes…', 'Short name', 'A considerably…')
    assert all(' · ' not in label for label in chart_labels(rows))


def test_real_261402_ranking_shows_four_previously_colliding_labels_distinctly(registry):
    ranking = largest_estimates(registry, '261402')
    labels = estimate_figure(ranking).layout.yaxis.ticktext
    assert len(set(labels)) == len(labels) == len(ranking.rows)
    assert labels[3:5] == ('Central Ter… · 4', 'Central Ter… · 5')
    assert labels[6:8] == ('MIA Concour… · 7', 'MIA Concour… · 8')


def test_collision_suffixes_change_no_hover_text_values_or_source_references(registry):
    ranking = largest_estimates(registry, '261402')
    before = [dict(row) for row in ranking.rows]
    trace = estimate_figure(ranking).data[0]
    assert ranking.rows == tuple(before)
    assert list(trace.y) == [row['project_id'] for row in ranking.rows]
    assert [custom[1] for custom in trace.customdata] == [row['project_name'] for row in ranking.rows]
    assert [custom[0] for custom in trace.customdata] == [row['source_ref'] for row in ranking.rows]
    assert [custom[2] for custom in trace.customdata] == [format_usd(row['estimate_usd']) for row in ranking.rows]
    assert list(trace.x) == [float(row['estimate_usd'] / Decimal('1000000')) for row in ranking.rows]
    assert '%{customdata[1]}' in trace.hovertemplate and 'Estimated cost' in trace.hovertemplate


def test_truncation_changes_no_values_table_or_financial_figures(registry):
    ranking = largest_estimates(registry, '261402')
    before = [dict(row) for row in ranking.rows]
    trace = estimate_figure(ranking).data[0]
    assert ranking.rows == tuple(before)
    assert list(trace.x) == [float(row['estimate_usd'] / Decimal('1000000')) for row in ranking.rows]
    assert [custom[0] for custom in trace.customdata] == [row['source_ref'] for row in ranking.rows]
    assert [custom[2] for custom in trace.customdata] == [format_usd(row['estimate_usd']) for row in ranking.rows]
    assert [custom[3] for custom in trace.customdata] == [row['pdf_page'] for row in ranking.rows]


def test_selection_rejects_stale_foreign_and_multiple_points(registry):
    ranking = largest_estimates(registry,'261402')
    point = {'customdata':[ranking.rows[1]['source_ref']]}
    assert selected_source_ref({'selection':{'points':[point]}},ranking) == ranking.rows[1]['source_ref']
    for points in ([],[{'customdata':['stale']}],[point,point],[{}],[{'customdata':'invalid'}]):
        assert selected_source_ref({'selection':{'points':points}},ranking) is None
