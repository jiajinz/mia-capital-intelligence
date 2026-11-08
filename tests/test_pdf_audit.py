"""Integration regressions over local pinned originals, skipped when unavailable."""

import importlib.util
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.integration


@pytest.fixture
def profiler():
    pytest.importorskip("pdfplumber")
    if not (ROOT / "data/raw/260526.pdf").is_file():
        pytest.skip("Pinned local PDF required. See docs/SOURCE_AUDIT.md.")
    spec = importlib.util.spec_from_file_location(
        "profiler_under_test", ROOT / "scripts/profile_infrastructure.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def source():
    return json.loads((ROOT / "data/source_inventory.json").read_text())["sources"][0]


def test_pinned_original_matches_row_controls(profiler, source) -> None:
    _, exhibit_b = profiler.profile(source, ROOT / "data/raw")
    assert len(exhibit_b) == 110


def test_reviewer_regex_omission_fails(profiler, source, monkeypatch) -> None:
    monkeypatch.setattr(
        profiler, "PROJECT_TOKEN",
        re.compile(r"(?!T180B$)" + profiler.PROJECT_TOKEN.pattern),
    )
    with pytest.raises(ValueError, match="ID grid and coordinate counts differ"):
        profiler.profile(source, ROOT / "data/raw")


def test_both_extraction_paths_omitting_same_row_fail(
    profiler, source, monkeypatch
) -> None:
    page_type = profiler.pdfplumber.page.Page
    original_words = page_type.extract_words
    original_table = page_type.find_table

    def filtered_words(page):
        return [word for word in original_words(page) if word["text"] != "T180B"]

    def filtered_table(page):
        table = original_table(page)
        return SimpleNamespace(
            columns=table.columns,
            extract=lambda: [row for row in table.extract() if row[0] != "T180B"],
        )

    monkeypatch.setattr(page_type, "extract_words", filtered_words)
    monkeypatch.setattr(page_type, "find_table", filtered_table)
    with pytest.raises(ValueError, match="expected 66 rows, found 65"):
        profiler.profile(source, ROOT / "data/raw")


def test_amount_swap_with_unchanged_page_total_fails(
    profiler, source, monkeypatch
) -> None:
    page_type = profiler.pdfplumber.page.Page
    original_crop = page_type.crop
    with profiler.pdfplumber.open(ROOT / "data/raw/260526.pdf") as pdf:
        anchors = {
            word["top"] - 1: word["text"]
            for word in pdf.pages[10].extract_words()
            if word["text"] in {"T180B", "T180D"} and word["x0"] < 81
        }
    swapped = {"T180B": "163,567,943", "T180D": "914,627,764"}

    def wrong_crop(page, bbox):
        if page.page_number == 11 and bbox[1] in anchors:
            return SimpleNamespace(extract_text=lambda: swapped[anchors[bbox[1]]])
        return original_crop(page, bbox)

    monkeypatch.setattr(page_type, "crop", wrong_crop)
    with pytest.raises(ValueError, match="expected ProfileRow.*T180B"):
        profiler.profile(source, ROOT / "data/raw")
