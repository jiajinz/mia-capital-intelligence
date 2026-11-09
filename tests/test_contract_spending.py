"""Exercise the Stage 2C input and display gate with temporary synthetic attestations."""

import json
import os
import shutil
from decimal import Decimal
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from mia_capital_intelligence import contract_spending as spending

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def local_root(tmp_path):
    path = tmp_path / spending.INPUT_PATH
    path.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / spending.INPUT_PATH, path)
    return tmp_path


@pytest.fixture
def synthetic_review(local_root):
    financial = spending.read_financial_input(local_root / spending.INPUT_PATH)
    return {
        "schema_version": "1.0",
        "decision": "approved",
        "reviewer_name": "Synthetic Test Reviewer",
        "reviewed_at": "2026-11-08T12:00:00-05:00",
        "input_sha256": financial.digest,
        "definition_version": spending.DEFINITION_VERSION,
        "definitions_accepted": True,
        "reviewed_source_refs": [row.source_ref for row in financial.rows],
        "evidence_reference": "Synthetic test fixture",
    }


def write_review(root, record):
    (root / spending.REVIEW_PATH).write_text(json.dumps(record))


def view(root, flag=None, address=None):
    return spending.financial_view(root, review_flag=flag, server_address=address)


def test_pending_gate_requires_both_local_flag_and_loopback(local_root):
    for flag, address in [(None, "127.0.0.1"), ("1", None), ("1", "0.0.0.0"), ("true", "127.0.0.1")]:
        result = view(local_root, flag, address)
        assert result.status == "pending_review" and not result.rows and not result.local_review
    result = view(local_root, "1", "127.0.0.1")
    assert result.status == "pending_review" and result.local_review and len(result.rows) == 12


@pytest.mark.parametrize(("field", "replacement", "expected"), [
    ("reviewer_name", " ", "invalid_review"),
    ("evidence_reference", "", "invalid_review"),
    ("reviewed_at", "2026-11-08T12:00:00", "invalid_review"),
    ("reviewed_at", "2099-01-01T00:00:00+00:00", "invalid_review"),
    ("definitions_accepted", 1, "invalid_review"),
    ("reviewed_source_refs", [], "invalid_review"),
    ("input_sha256", "0" * 64, "stale_review"),
    ("definition_version", "contract-expenditures-0.9", "stale_review"),
])
def test_invalid_and_stale_review_hide_all_rows(local_root, synthetic_review, field, replacement, expected):
    synthetic_review[field] = replacement
    write_review(local_root, synthetic_review)
    result = view(local_root)
    assert result.status == expected and not result.rows


def test_review_digest_and_all_row_refs_enable_ordinary_read_only_view(local_root, synthetic_review):
    write_review(local_root, synthetic_review)
    result = view(local_root, address="0.0.0.0")
    assert result.status == "approved" and not result.local_review and len(result.rows) == 12
    assert len({(row.contract_id, row.reported_month) for row in result.rows}) == 12
    row = next(row for row in result.rows if row.contract_id == "A19-MDAD-02" and row.reported_month == "2026-09")
    assert row.monthly_usd == Decimal("98135.01") and row.cumulative_usd == Decimal("13671042.69")
    assert row.financial_url.endswith("261400.pdf#page=30")
    zeros = [row for row in result.rows if row.monthly_dash_corroborated]
    assert len(zeros) == 4 and all(row.monthly_usd == Decimal("0.00") for row in zeros)
    e20 = next(row for row in zeros if row.contract_id == "E20-MDAD-03")
    assert e20.raw_contract == "E20-MDAD--03" and e20.summary_url.endswith("261400.pdf#page=22")


def test_altered_artifact_fails_even_in_local_review(local_root, synthetic_review):
    write_review(local_root, synthetic_review)
    path = local_root / spending.INPUT_PATH
    path.write_bytes(path.read_bytes() + b"\n")
    result = view(local_root, "1", "127.0.0.1")
    assert result.status == "invalid_input" and not result.rows


@pytest.mark.integration
def test_pinned_pdf_rebuild_is_reproducible_and_failure_preserves_valid_output(tmp_path):
    pdf_dir = os.environ.get("MIA_STUDY_PDF_DIR")
    if pdf_dir is None:
        pytest.skip("Set MIA_STUDY_PDF_DIR to the three pinned study PDFs")
    original = ROOT / spending.INPUT_PATH
    output = tmp_path / "financial.json"
    spending.build_financial_input(original, Path(pdf_dir), output)
    assert output.read_bytes() == original.read_bytes()
    data = json.loads(original.read_bytes())
    for issue in data["sources"]:
        first, second = issue["records"][:2]
        for field in ("raw_cells_visual", "summary_expenditures"):
            first[field], second[field] = second[field], first[field]
    candidate = tmp_path / "candidate.json"
    candidate.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Financial PDF row binding mismatch"):
        spending.build_financial_input(candidate, Path(pdf_dir), output)
    assert output.read_bytes() == original.read_bytes()


def app_for(monkeypatch, root, *, loopback=False):
    import streamlit as st

    original_view = spending.financial_view
    monkeypatch.setattr(spending, "financial_view", lambda _root, **options: original_view(root, **options))
    original_option = st.get_option
    if loopback:
        monkeypatch.setattr(st, "get_option", lambda option: (
            "127.0.0.1" if option == "server.address" else original_option(option)
        ))
    return AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=15)


def test_browser_request_parameter_cannot_unlock_pending_data(monkeypatch, local_root):
    monkeypatch.delenv("MIA_FINANCIAL_LOCAL_REVIEW", raising=False)
    app = app_for(monkeypatch, local_root, loopback=True)
    app.query_params["MIA_FINANCIAL_LOCAL_REVIEW"] = "1"
    app.query_params["local_review"] = "1"
    app.run()
    assert not app.exception
    tab = app.tabs[3]
    assert "pending named independent review" in tab.info[0].value
    assert not tab.get("plotly_chart") and not tab.selectbox and not tab.dataframe and not tab.get("link_button")


def test_local_preview_displays_banner_and_explicit_summary_zero(monkeypatch, local_root):
    monkeypatch.setenv("MIA_FINANCIAL_LOCAL_REVIEW", "1")
    app = app_for(monkeypatch, local_root, loopback=True).run()
    assert not app.exception
    tab = app.tabs[3]
    assert "Named independent review pending" in tab.warning[0].value
    assert tab.dataframe[0].value["Monthly expenditures"].tolist() == ["$80,212.05", "$103,511.27", "$98,135.01"]
    app.selectbox(key="spending_contract").set_value("E20-MDAD-03").run()
    assert not app.exception
    tab = app.tabs[3]
    last = tab.dataframe[0].value.iloc[-1]
    assert last["Monthly expenditures"] == "$0.00"
    assert last["Monthly cell evidence"] == "Dash corroborated by summary zero"
    assert last["Summary PDF"].endswith("261400.pdf#page=22")
    assert len(tab.get("plotly_chart")) == 1


def test_ordinary_reviewed_app_shows_chart_without_preview_banner(monkeypatch, local_root, synthetic_review):
    monkeypatch.delenv("MIA_FINANCIAL_LOCAL_REVIEW", raising=False)
    write_review(local_root, synthetic_review)
    app = app_for(monkeypatch, local_root).run()
    assert not app.exception
    tab = app.tabs[3]
    assert len(tab.get("plotly_chart")) == 1 and not tab.warning
    assert tab.dataframe[0].value.iloc[-1]["Cumulative expenditures"] == "$13,671,042.69"
