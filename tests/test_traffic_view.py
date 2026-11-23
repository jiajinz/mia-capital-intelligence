"""Loader, year-on-year, and chart checks for the admitted monthly traffic series."""

import json
import shutil
from decimal import Decimal
from pathlib import Path

import pytest

from mia_capital_intelligence.traffic_view import (
    DATA_DIR, expected_periods, load_traffic_series, comparable_years, traffic_figure, year_comparison,
    year_figure,
)

GAP_PERIODS = ("2010-07", "2013-06")


@pytest.fixture(scope="module")
def series():
    return load_traffic_series()


def test_loader_reproduces_199_admitted_months_from_2010_01_to_2026_09(series):
    periods = [month.period for month in series.months]
    assert len(expected_periods()) == 201
    assert len(periods) == 199
    assert periods == sorted(periods)
    assert periods[0] == "2010-01" and periods[-1] == "2026-09"
    assert set(periods) == set(expected_periods()) - set(GAP_PERIODS)


def test_gap_and_held_months_are_reported_with_reasons_not_dropped(series):
    assert [(item.period, item.status) for item in series.unavailable] == [("2010-07", "gap"), ("2013-06", "held")]
    assert series.unavailable[0].reason == "No admitted value in the traffic data files"
    assert "CYTD step differs from total" in series.unavailable[1].reason
    assert series.all_periods() == expected_periods()


def test_exact_values_and_sources_for_admitted_months(series):
    by_period = series.by_period()
    january_2010 = by_period["2010-01"]
    assert january_2010.passengers.value == 3032886
    assert january_2010.cargo_tons.value == 149901
    assert january_2010.seats.value == 3789839
    assert january_2010.commercial_movements.value == 31968
    assert january_2010.passengers.source_file == "monthly_traffic_jan_2010.asp"
    assert january_2010.passengers.pdf_page is None
    assert january_2010.passengers.dataset_file == "traffic_monthly.html_2010_2017.v1.json"

    january_2018 = by_period["2018-01"]
    assert january_2018.passengers.value == 3956962
    assert january_2018.cargo_tons.value == 196352
    assert january_2018.passengers.source_file == "January_2018_Monthly_Calendar_Traffic_Report.pdf"
    assert january_2018.passengers.pdf_page == 1
    assert january_2018.passengers.revised is False


def test_all_values_are_exact_integers_never_floats(series):
    for month in series.months:
        for field in (month.passengers, month.cargo_tons, month.seats, month.commercial_movements):
            assert type(field.value) is int
            assert field.value >= 0


def test_revised_values_are_flagged_and_labelled(series):
    revised = [month.period for month in series.months
               if month.passengers.revised or month.cargo_tons.revised or month.seats.revised]
    assert revised == ["2025-03"]
    march_2025 = series.by_period()["2025-03"]
    assert march_2025.passengers.value == 5141796
    assert march_2025.cargo_tons.value == 270818
    assert march_2025.passengers.revised and march_2025.cargo_tons.revised
    assert march_2025.passengers.note == "Revised report; first-published version not obtained"
    assert "Revised" in march_2025.passengers.source_file


def test_prior_year_column_values_carry_their_printed_origin(series):
    october_2018 = series.by_period()["2018-10"].passengers
    assert october_2018.note == "Prior-year column of the 2019-10 report"
    assert series.by_period()["2024-01"].passengers.note == ""


def test_year_comparison_uses_exact_integer_change_and_decimal_percent(series):
    january, february, march = year_comparison(series, 2025, "passengers")[:3]
    assert (january.current, january.prior, january.change) == (5067376, 5035404, 31972)
    assert january.percent == Decimal("0.6")
    assert march.percent == Decimal("-1.2")
    assert isinstance(march.percent, Decimal)


def test_year_comparison_leaves_months_outside_the_series_blank(series):
    october_2026 = year_comparison(series, 2026, "passengers")[9]
    assert october_2026.current is None
    assert october_2026.change is None and october_2026.percent is None
    assert comparable_years(series)[0] == 2011
    assert comparable_years(series)[-1] == 2026


def test_figure_labels_both_gaps_and_the_pandemic_break(series):
    figure = traffic_figure(series)
    texts = [annotation.text for annotation in figure.layout.annotations]
    assert "Gap 2010-07" in texts and "Held 2013-06" in texts
    assert "Pandemic break, Mar 2020 to Dec 2021" in texts
    shaded = [shape for shape in figure.layout.shapes if shape.type == "rect"]
    assert any(shape.x0 == "2020-03-01" and shape.x1 == "2022-01-01" for shape in shaded)
    periods = expected_periods()
    main_lines = [trace for trace in figure.data if trace.mode == "lines"]
    assert len(main_lines) == 2
    for trace in main_lines:
        assert len(trace.y) == 201
        assert trace.y[periods.index("2010-07")] is None
        assert trace.y[periods.index("2013-06")] is None
        assert trace.y[periods.index("2013-05")] is not None


def test_year_figure_separates_prior_year_by_dash_not_colour_alone(series):
    figure = year_figure(series, 2025, "cargo_tons")
    prior, current = figure.data
    assert prior.name == "2024" and current.name == "2025"
    assert prior.line.dash == "dash"
    assert current.line.dash in (None, "solid")
    assert list(prior.x) == ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def copy_data(tmp_path: Path) -> Path:
    target = tmp_path / "traffic"
    shutil.copytree(DATA_DIR, target)
    return target


def edit_rows(path: Path, mutate) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    mutate(document)
    path.write_text(json.dumps(document), encoding="utf-8")


def test_loader_rejects_duplicate_admitted_values(tmp_path):
    target = copy_data(tmp_path)
    plan_a = target / "traffic_monthly.plan_a.v1.json"
    edit_rows(plan_a, lambda document: document["rows"].append(dict(document["rows"][0])))
    with pytest.raises(ValueError, match="Duplicate admitted value for 2024-01 PASSENGERS"):
        load_traffic_series(target)


def test_loader_rejects_a_month_with_only_some_measures(tmp_path):
    target = copy_data(tmp_path)
    plan_a = target / "traffic_monthly.plan_a.v1.json"
    edit_rows(plan_a, lambda document: document.update(rows=[
        row for row in document["rows"] if not (row["period"] == "2024-01" and row["measure"] == "PASSENGERS")
    ]))
    with pytest.raises(ValueError, match="2024-01 has only some admitted measures"):
        load_traffic_series(target)


def test_loader_rejects_a_dataset_that_is_not_admitted(tmp_path):
    target = copy_data(tmp_path)
    edit_rows(target / "traffic_monthly.gap_2015_2017.v1.json", lambda document: document.update(status="held"))
    with pytest.raises(ValueError, match="is not an admitted traffic dataset"):
        load_traffic_series(target)
