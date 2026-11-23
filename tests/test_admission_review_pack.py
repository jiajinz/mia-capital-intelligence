"""Review pack for one candidate traffic admission: passing, blocking and deterministic cases.

The one-page fixture reuses page_lines and extract_rows from test_traffic_pilot. No PDF is read.
"""
from __future__ import annotations

import calendar
import importlib.util
import json
from pathlib import Path

import pytest

from mia_capital_intelligence import traffic_pilot as traffic
from test_traffic_pilot import page_lines

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_review_pack.py"
SPEC = importlib.util.spec_from_file_location("build_review_pack", SCRIPT)
assert SPEC and SPEC.loader
pack_script = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pack_script)


def fake_read_page(body: bytes, period: str) -> list[dict]:
    """Stand in for the PDF reader: the body is a JSON spec for a synthetic page."""
    spec = json.loads(body)
    year, month = map(int, spec["printed"].split("-"))
    lines = page_lines()
    lines[1] = (f"MONTH ENDED: {calendar.month_name[month].upper()} "
                f"{calendar.monthrange(year, month)[1]}, {year}", lines[1][1])
    if spec.get("passenger_cytd") is not None:
        combined = [cells for text, cells in lines if text.startswith("PASSENGERS ")][-1]
        combined[6]["text"] = str(spec["passenger_cytd"])  # CYTD is numbers[5], after the one-word label
    return traffic.extract_rows(lines, period)


@pytest.fixture(autouse=True)
def synthetic_reader(monkeypatch):
    monkeypatch.setattr(traffic, "read_page", fake_read_page)


def candidate_folder(tmp_path: Path, *specs: dict) -> Path:
    folder = tmp_path / "candidates"
    folder.mkdir()
    for index, spec in enumerate(specs):
        (folder / f"candidate-{index}.pdf").write_bytes(json.dumps(spec, sort_keys=True).encode())
    return folder


def admitted_row(period: str, measure: str, value: int, sha: str = "a" * 64) -> dict:
    return {"period": period, "market": "COMBINED TOTALS", "measure": measure, "value": value,
            "source_sha256": sha, "vintage": {"first_published": {"status": "single_version_observed"}}}


def admitted_file(tmp_path: Path, rows: list[dict], rule: str = "two_vintages") -> Path:
    path = tmp_path / "admitted.json"
    path.write_text(json.dumps({"dataset_version": "synthetic-test", "revision_rule": rule, "rows": rows}))
    return path


def prior_year_rows(value: int = 2) -> list[dict]:
    # The synthetic page reports 2 as the prior-year same-month value for both measures.
    return [admitted_row("2024-01", measure, value) for measure in pack_script.SCOPE]


def test_passing_pack_records_checks_rows_and_page_references(tmp_path):
    folder = candidate_folder(tmp_path, {"printed": "2025-01"})
    pack = pack_script.build_pack(folder, "2025-01", admitted_file(tmp_path, prior_year_rows()))
    assert all(item["pass"] for item in pack["checks"])
    assert {item["id"] for item in pack["checks"]} == {
        "period_evidence", "printed_month_end", "two_vintage_rule", "deplaned_plus_enplaned_equals_total",
        "cytd_rule", "prior_year_same_month"}
    assert pack["source_documents"][0]["file"] == "candidate-0.pdf"
    assert len(pack["source_documents"][0]["sha256"]) == 64
    assert [row["measure"] for row in pack["rows"]] == list(pack_script.SCOPE)
    assert all(row["page_reference"]["page_index"] == 0 for row in pack["rows"])
    assert all(row["page_reference"]["table_header"] for row in pack["rows"])
    assert pack["diff_against_admitted"]["status"] == "new_period"
    assert pack["diff_against_admitted"]["changes"] == []


def test_failing_cytd_check_blocks_the_pack(tmp_path):
    folder = candidate_folder(tmp_path, {"printed": "2025-01", "passenger_cytd": 5})
    out = tmp_path / "pack.json"
    with pytest.raises(pack_script.ReviewRefused, match="cytd_rule"):
        pack_script.build_pack(folder, "2025-01", admitted_file(tmp_path, prior_year_rows()))
    assert pack_script.main(["--folder", str(folder), "--period", "2025-01", "--admitted",
                             str(admitted_file(tmp_path, prior_year_rows())), "--out", str(out)]) == 2
    assert not out.exists()


def test_missing_period_blocks_the_pack(tmp_path):
    folder = candidate_folder(tmp_path, {"printed": "2024-12"})
    out = tmp_path / "pack.json"
    with pytest.raises(pack_script.ReviewRefused, match="no candidate PDF"):
        pack_script.build_pack(folder, "2025-01", admitted_file(tmp_path, prior_year_rows()))
    assert pack_script.main(["--folder", str(folder), "--period", "2025-01", "--admitted",
                             str(admitted_file(tmp_path, prior_year_rows())), "--out", str(out)]) == 2
    assert not out.exists()


def test_output_is_deterministic(tmp_path):
    folder = candidate_folder(tmp_path, {"printed": "2025-01"})
    admitted = admitted_file(tmp_path, prior_year_rows())
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    for out in (first, second):
        pack_script.write_pack(out, pack_script.build_pack(folder, "2025-01", admitted))
    assert first.read_bytes() == second.read_bytes()
    assert str(tmp_path) not in first.read_text()


def test_pack_refuses_to_write_inside_the_repository(tmp_path):
    inside = pack_script.ROOT / "review-pack-should-not-exist.json"
    with pytest.raises(pack_script.ReviewRefused, match="inside the repository"):
        pack_script.write_pack(inside, {"period": "2025-01"})
    assert not inside.exists()


def test_revised_source_is_listed_for_follow_up_not_refused(tmp_path):
    folder = candidate_folder(tmp_path, {"printed": "2025-01"})
    rows = prior_year_rows() + [admitted_row("2025-01", measure, 1, sha="b" * 64) for measure in pack_script.SCOPE]
    pack = pack_script.build_pack(folder, "2025-01", admitted_file(tmp_path, rows))
    diff = pack["diff_against_admitted"]
    assert diff["status"] == "revised_source"
    assert {(c["measure"], c["before"], c["after"]) for c in diff["changes"]} == {
        ("PASSENGERS", 1, 4), ("TOTAL CARGO-TONS", 1, 8)}
    assert len(diff["follow_up_requests"]) == 2
    assert diff["first_published_retained"]["status"] == "single_version_observed"


def test_non_january_cytd_sums_admitted_months_with_tonnage_rounding():
    row = {"measure": "PASSENGERS", "value": 40, "raw": {"cytd": "140", "deplaned": "20", "enplaned": "20",
                                                         "same_month_prior_year": "2"}}
    tons = {"measure": "TOTAL CARGO-TONS", "value": 40, "raw": {"cytd": "141", "deplaned": "20",
                                                                "enplaned": "20", "same_month_prior_year": "2"}}
    earlier = {"period": "2024-01", "market": "COMBINED TOTALS", "value": 100, "source_sha256": "c" * 64}
    admitted_rows = [dict(earlier, measure="PASSENGERS"), dict(earlier, measure="TOTAL CARGO-TONS")]
    admitted = pack_script.Admitted("synthetic.json", "d" * 64, "synthetic-test", "two_vintages",
                                    {(r["period"], r["market"], r["measure"]): r for r in admitted_rows})
    assert pack_script.cytd_check("2024-02", row, admitted, "scope")["pass"] is True
    assert pack_script.cytd_check("2024-02", tons, admitted, "scope")["pass"] is True
    tons["raw"]["cytd"] = "142"
    assert pack_script.cytd_check("2024-02", tons, admitted, "scope")["pass"] is False
    row["raw"]["cytd"] = "139"
    assert pack_script.cytd_check("2024-02", row, admitted, "scope")["pass"] is False
