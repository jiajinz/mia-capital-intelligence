"""Research evidence must reconcile before supporting a feasibility conclusion."""
import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
check_study = runpy.run_path(str(ROOT / 'scripts/check_financial_feasibility.py'))['check_study']


@pytest.fixture
def study():
    return json.loads((ROOT / 'docs/research/financial_snapshots.json').read_text())


def test_three_months_and_all_five_columns_reconcile(study):
    result = check_study(study)
    assert len(result) == 3
    assert [row['column_totals']['monthly_expenditures_usd'] for row in result] == ['537673.09','206061.07','194680.63']


@pytest.mark.parametrize('defect', ['missing_row','duplicate_id','monthly_error','unresolved_dash','summary_mismatch','total_error','broken_rollforward','reordered_months'])
def test_research_defects_fail_closed(study,defect):
    source = study['sources'][1]
    row = source['records'][0]
    if defect == 'missing_row': source['records'].pop()
    elif defect == 'duplicate_id': source['records'][1]['contract_id'] = row['contract_id']
    elif defect == 'monthly_error': row['raw_cells_visual']['monthly_expenditures_usd'] = '103,511.28'
    elif defect == 'unresolved_dash': source['records'][3]['dash_resolution'] = None
    elif defect == 'summary_mismatch': row['summary_expenditures']['monthly_expenditures_usd'] = '0.00'
    elif defect == 'total_error': source['printed_totals']['monthly_expenditures_usd'] = '206,061.08'
    elif defect == 'reordered_months': study['sources'].reverse()
    elif defect == 'broken_rollforward':
        for fields in ('raw_cells_visual','summary_expenditures'):
            row[fields]['prior_expenditures_usd'] = '13,469,396.40'
            row[fields]['monthly_expenditures_usd'] = '103,511.28'
    with pytest.raises(ValueError): check_study(study)
