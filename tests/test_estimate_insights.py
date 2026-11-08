"""Protect the chart's population, exact ranking and evidence navigation."""
from dataclasses import replace
from decimal import Decimal

import pytest

from mia_capital_intelligence.estimate_insights import estimate_figure, largest_estimates, selected_source_ref
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
    trace = estimate_figure(ranking).data[0]
    assert trace.orientation == 'h'
    assert trace.customdata[0][0] == ranking.rows[0]['source_ref']
    assert trace.customdata[0][2] == '$ 1,066,231,593'
    assert list(trace.x) == [float(row['estimate_usd']) for row in ranking.rows]
    assert 'Estimated cost' in trace.hovertemplate


def test_selection_rejects_stale_foreign_and_multiple_points(registry):
    ranking = largest_estimates(registry,'261402')
    point = {'customdata':[ranking.rows[1]['source_ref']]}
    assert selected_source_ref({'selection':{'points':[point]}},ranking) == ranking.rows[1]['source_ref']
    for points in ([],[{'customdata':['stale']}],[point,point],[{}],[{'customdata':'invalid'}]):
        assert selected_source_ref({'selection':{'points':points}},ranking) is None
