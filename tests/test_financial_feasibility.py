"""Research evidence must reconcile before supporting a feasibility conclusion."""
import json
import os
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
check_study = runpy.run_path(str(ROOT / 'scripts/check_financial_feasibility.py'))['check_study']


@pytest.fixture
def study():
    return json.loads((ROOT / 'data/financial/snapshots.v1.json').read_text())


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


@pytest.fixture
def study_pdfs():
    directory = os.environ.get("MIA_STUDY_PDF_DIR")
    if directory is None:
        pytest.skip("Set MIA_STUDY_PDF_DIR to the three pinned study PDFs")
    return Path(directory)


@pytest.mark.integration
def test_pinned_pdf_controls_bind_all_three_issues(study, study_pdfs):
    assert len(check_study(study, study_pdfs)) == 3


@pytest.mark.integration
@pytest.mark.parametrize("defect", [
    "wrong_financial_page", "wrong_summary_page", "wrong_summary_row", "wrong_column",
    "unrelated_zero_note", "zero_from_other_contract", "full_series_row_reassociation",
])
def test_study_binding_rejects_mutations_that_preserve_arithmetic(study, study_pdfs, defect):
    july, august, september = study["sources"]
    e20 = september["records"][2]
    if defect == "wrong_financial_page":
        august["financial_pdf_page"] = 1
    elif defect == "wrong_summary_page":
        e20["summary_pdf_page"] = 1
    elif defect == "wrong_summary_row":
        e20["summary_row_ordinal"] = 2
    elif defect == "wrong_column":
        headings = august["columns"]
        adopted, approved = "adopted_budget_usd", "approved_budget_usd"
        headings[adopted], headings[approved] = headings[approved], headings[adopted]
    elif defect == "unrelated_zero_note":
        e20["dash_resolution"] = "Unrelated nonempty note"
    elif defect == "zero_from_other_contract":
        v009a = september["records"][3]
        e20["summary_pdf_page"] = v009a["summary_pdf_page"]
        e20["summary_row_ordinal"] = v009a["summary_row_ordinal"]
    elif defect == "full_series_row_reassociation":
        for issue in (july, august, september):
            first, second = issue["records"][:2]
            for field in ("raw_cells_visual", "summary_expenditures"):
                first[field], second[field] = second[field], first[field]
        assert len(check_study(study)) == 3  # The amounts still reconcile arithmetically.
    with pytest.raises(ValueError, match="binding mismatch|Unsupported dash resolution"):
        check_study(study, study_pdfs)
