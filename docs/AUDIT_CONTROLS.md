# Stage 0 row control evidence

## Coverage and method

`data/audit/exhibit_b_row_controls.csv` contains 222 row controls for 260526 Exhibit B pp. 11–12 and 261402 Exhibit B pp. 12–13. Each record retains the PDF checksum, exhibit, PDF position, printed MDC label, one-based data-row ordinal, exact project token and reported whole-dollar estimate. Rows are in physical source order. Preserve phase suffixes and punctuation. This is a checked-in extraction control with machine cross-check status. Human review of each original row and scope approval remain pending.

The control was constructed on November 8, 2026 using pypdfium2 5.14.0 against the previously pinned local originals. PDFium reads every nonempty line of the ID column without a project-ID regular expression or pdfplumber table grid. It locates that exact full ID-column value on the page and reads the amount at the same vertical position from a fixed amount column. Exact whole-dollar conversion uses integers. Matching the full column value keeps AB041A distinct from AB041A-1. The source bytes are checked before opening them.

The separate pdfplumber profiler matches all 222 ordered ID/amount pairs against this frozen control. Earlier page counts and totals are 66 / 2,955,660,025 USD and 44 / 3,446,491,140 USD. Later they are 68 / 3,356,850,420 USD and 44 / 3,406,481,145 USD. The sums are extraction controls, with no inferred full-airport coverage. The user-provided independent review also reports agreement on all 222 rows using PDFium, but provided no row-level file to import. This repository's control is a fresh extraction with its own reproducible method.

The two methods use separate PDF engines and ID discovery logic. They still read the same PDFs and rely on measured column bands. Agreement provides a regression baseline and supports extraction consistency. A reviewer must still confirm the source rows, measure semantics and project scope before pilot publication. Exhibit A remains exploratory, with grid/anchor checks and page subtotals, and has no frozen independent amount ledger.

## Replay

Install the optional pinned top-level audit dependencies and run from the repository root.

```sh
.venv/bin/python -m pip install -r requirements-audit.txt
PYTHONPATH=src .venv/bin/python scripts/check_exhibit_b_controls.py
PYTHONPATH=src .venv/bin/python scripts/profile_infrastructure.py
.venv/bin/python -m pytest -q
```

The PDFium command validates the existing control and emits one matched-row count per page. It leaves the control file intact. The profiler rejects any ordered ID/amount disagreement, even if the page total matches. Its raw grid-ID check also examines each non-heading row without the anchor regex, catching an anchor filter that omits an entire project. Unexpected changes require adjudication against the pinned original and a separately reviewed control-file change.

## Regression and debugging

`tests/test_pdf_audit.py` exercises the real pinned early PDF when the optional library and local original are available. It covers the reviewer's T180B regex omission, simultaneous omission in both discovery paths, and swapping T180B/T180D amounts while preserving the subtotal. Each must raise before a source's success summary is printed. `tests/test_row_controls.py` independently tests missing, duplicated and reordered rows, wrong amounts, null amounts, and control provenance. Offline unit fixtures remain synthetic. Integration skips are explicit when the local audit inputs are absent.

In PyCharm use the repository `.venv`, target `tests/test_pdf_audit.py` with pytest and set the working directory to the repository root. Debug the simultaneous-omission or same-total-swap test. Break at `validate_page_rows` and compare the actual page with the fixed controls. The row-count failure catches the shared omission, and the ordered ID/amount failure catches the swap. The profiler is read-only and has no published output bundle. Atomic publication and rollback tests belong to the proposed Stage 1 implementation.
