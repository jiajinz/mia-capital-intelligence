# Independent review packet — Stage 0

## Corrective handoff — November 8, 2026

The owner provided a CONDITIONAL PASS review of `55f6e39e630c18dc5e61672965dfef4bf7b72e3c`. The material findings were checked against the actual repository. Stage 1 authorization is still pending. This project is independent of MDAD and HNTB.

- **P1-01 accepted, audit correction implemented.** The original shared regex omitted T180B from both paths and returned 65 rows / 2,041,032,261 USD on early B p. 11 without raising. The profiler now checks every non-heading grid ID independently of the anchor regex and matches all ordered B ID/amount pairs to a frozen control. A newly implemented PDFium check reproduces all 222 row controls. Three real-PDF corruption regressions reject the reviewer's regex omission, omission from both extraction paths, and T180B/T180D amount swaps with an unchanged subtotal. Independent human row confirmation remains a publication prerequisite.
- **P1-02 accepted, design contract recorded, executable enforcement pending Stage 1.** All 107 pairs, including equal amounts, require a disposition. Missing scope, measure or estimate-basis approval means held with null comparison deltas. CA176A/B, T180B/T180D and BA133A are specified examples. Reviewer identity, reason and both immutable source references are required. See `docs/SCOPE_REVIEW_CONTRACT.md` for the full contract and future acceptance tests. This correction supplies no approved real comparison or pilot query.
- **P2-01 accepted in part for immediate correction.** The sequential acquisition example now verifies the temporary PDF's signature, size and SHA-256 before replacement. Source freeze dates remain unknown, including the documented AA005A date discrepancy. The owner's existing README edit is preserved and excluded from this commit. Owner confirmation of its shorter affiliation disclosure remains open.

### Changed files and key entry points

- `data/audit/exhibit_b_row_controls.csv` stores the 222 pinned source-row controls. `docs/AUDIT_CONTROLS.md` records their method, status and replay instructions. Raw PDFs remain ignored.
- `src/mia_capital_intelligence/row_controls.py:16` loads versioned page controls. `validate_page_rows` at line 38 rejects count, ordered-ID or amount differences.
- `scripts/profile_infrastructure.py:26` validates each B page against the control before a source success summary. `scripts/check_exhibit_b_controls.py` rechecks the frozen file using a second PDF engine and ID discovery method. It does not regenerate the control automatically.
- `tests/test_row_controls.py`, `tests/test_pdf_audit.py`, `pyproject.toml`, and `requirements-audit.txt` add unit and real-input regressions and document optional dependencies.
- `docs/PROJECT_STATE.md`, `docs/DECISIONS.md`, `docs/SOURCE_AUDIT.md` and this packet record the review decisions, remaining limits and corrected acquisition procedure.

### Actual validation and review evidence

Python 3.13.1 ran **25 passing tests**, including four real-input integration tests. `PYTHONPATH=src .venv/bin/python scripts/check_exhibit_b_controls.py` matched 66, 44, 68 and 44 row controls on the four pinned B pages. `PYTHONPATH=src .venv/bin/python scripts/profile_infrastructure.py` reproduced the ten page controls and the 107 paired / 3 earlier-only / 5 later-only B counts. The independent control covers each `(source checksum, exhibit, page, ordinal, project ID, amount)` association. Exhibit A's amount controls remain exploratory.

For review without a checkout, inspect these selected fixed CSV records against the official PDFs below. `T180B` is early B p. 11 row 63 at 914,627,764 USD and later B p. 12 at 1,066,231,593 USD. `T180D` immediately follows the early T180B row at 163,567,943 USD. In the swap regression those amounts exchange IDs, retaining the subtotal. `validate_page_rows` fails on the first differing association. The full 222-record CSV is small enough to share with this packet and the corrective diff.

The control is machine cross-checked against the existing local source bytes. It has no per-row human signature or scope approval. The owner's review reports another independent 222-row PDFium match and selected visual checks, with no fresh-download byte comparison. This corrective session reused the pinned originals and leaves full human confirmation pending.

### Commit and remaining review

Branch `main`. Corrective subject `fix(audit): reject omitted and misbound Exhibit B rows`. Resolve the exact hash with `git log -1 --format='%H %s' -- scripts/profile_infrastructure.py`; inspect with `git show <resolved-hash>`. The reviewed original baseline remains `55f6e39e630c18dc5e61672965dfef4bf7b72e3c`. Share the corrective diff, this packet and `data/audit/exhibit_b_row_controls.csv` for external review.

Review whether the independently captured row controls and omission/swap tests adequately close the reported extraction failure. Confirm the scope-review contract before owner authorization of Stage 1. P1-02 implementation, all 107 pair dispositions, human evidence confirmation and future output publication/rollback validation remain open.

## Objective and acceptance

Establish whether the three specified county records can support evidence-based project follow-up, with traceable source versions, real table checks, documented limits, a runnable Python baseline and a small next-stage design. This packet is intended for a reviewer with access to public PDFs and the text provided by the owner.

## Delivered and where to look

- `AGENTS.md` records engineering, data and review constraints. `README.md` gives Python and PyCharm setup.
- `data/source_inventory.json` pins three source versions, reporting bases and date roles, plus evidence page ranges and printed labels.
- `docs/SOURCE_AUDIT.md` gives page checks, financial reconciliation, examples, coverage and commands. `docs/DATA_DICTIONARY.md` specifies grain, field meanings and null policy. `docs/DECISIONS.md` records the DuckDB decision and Stage 1 acceptance.
- `src/mia_capital_intelligence/source_identity.py:8`, `verify_pdf`, checks the PDF signature, byte count and SHA-256. The baseline `profile` function anchored the estimate to an ID's position and checked grid token counts. The correction above adds an independent row-control gate. `tests/test_source_identity.py` exercises manifest consistency and byte verification with synthetic inputs.

## Review without a local checkout

Download and open the official sources. Page references here are one-based PDF positions, with printed MDC labels in parentheses.

- [260526](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/260526.pdf) — memo p. 1 covers October–December 2025. A pp. 8–10 and B pp. 11–12. SHA-256 `eaf845f4fb746a69940f38fe4655d27b56ab42effdbf9cfdd1dbc746a0fba878`.
- [261402](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261402.pdf) — memo p. 2 covers January–March 2026. A pp. 9–11 and B pp. 12–13. SHA-256 `84751b451da8b7d5e06cad6b1c24c870e563de5669c5f07325033c446bbaeb2a`.
- [261400](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261400.pdf) — September 2026. Summary pp. 21–22 and financial table p. 30, internally Page 1 of 1. SHA-256 `ae45ec3eeaf1f54df04ad2255ed9ec3c0f3f647d3b2570b39272ff75efe9f9ae`.

Representative evidence (selected cells transcribed from rendered originals):

- **T180B, B**. 260526 p. 11 (MDC011) shows estimate 914,627,764 and substantial completion 27-Aug-30. 261402 p. 12 (MDC012) shows 1,066,231,593 and 22-Nov-30. The later separate completion field reads 20-Jul-31. Signed estimate change is 151,603,829, or 16.58% using the earlier estimate as denominator. The reported substantial milestone moves 87 days. Ask which scope and estimate assumptions the two numbers share before making a finding.
- **X133A, A**. 260526 p. 10 (MDC010) shows Terminal D Computer Room, 2,711,000, and NOT FUNDED. 261402 p. 10 (MDC010) adds Building 3030 to the description and shows 13,374,558. Earlier Y023A identifies a Building 3030 computer-room row. The pair is held for scope review. Possible consolidation remains unverified.
- **D105C-I**. 261402 pp. 9 and 12 both show 19,797,252 for parking garage elevator modernization. Cross-exhibit addition would include that amount twice.
- **E20-MDAD-03**. 261400 p. 22 (MDC022) shows prior and cumulative 5,543,728.88 and current month 0.00. The equivalent p. 30 row adds a hyphen in the printed ID and displays a dash for the month. Reconciliation uses the summary's explicit zero with a manual match.

## Actual audit results and verification

- Exhibit B has 110 earlier and 112 later rows, with 107 exact token overlaps. Earlier page counts and estimate sums are 66 / $2,955,660,025 and 44 / $3,446,491,140. Later they are 68 / $3,356,850,420 and 44 / $3,406,481,145. This is a row-level audit control. Changed coverage, scope or basis can affect the difference between exhibit sums.
- Exhibit A has 139 earlier and 165 later rows, with 137 exact token overlaps. The printed placeholder TBD-007 accounts for $525,120,616 of later A. IDs are unique within each of the four exhibits. A/B overlap and possible scope changes prevent an airport-wide aggregation. A printed estimate dash remains missing.
- Line-grid and separate position-based ID extraction methods agreed across the ten quarterly pages. Amounts were profiled by cell position and representative rows, the top four absolute B changes and top A change were visually checked. The quarterly exhibits supply no located grand total. A second-person reconciliation of the full amount columns is still required.
- For September, prior + current = cumulative for all four rows. Row sums agree with all five printed totals. The cumulative total is $41,921,175.59. The adopted budget, current approved budget, award values and expenditure measures retain separate definitions.
- Pytest on Python 3.13.1 passed all nine tests. The optional profile reproduced the ten page controls against pinned originals. Tests cover inventory structure, adjacent quarterly memo periods, and rejection of signature/size/hash mismatches. They do not attest to project scope, table correctness or financial semantics.
- Locally run `.venv/bin/python -m pytest -q` and `PYTHONPATH=src .venv/bin/python scripts/profile_infrastructure.py` after following the source audit setup. To reproduce independently, compare checksums, recount and double-key the B pages, then calculate T180B using the two displayed cells and compare each monthly row with pp. 21–22.

## Limits and review questions

1. Is a same-exhibit, same-token candidate join plus a scope review sufficient for the first estimate-change query? Check CA176A/B and CA096A for examples of changes the key alone cannot resolve.
2. Can the source owner confirm the actual marker and applicable freeze dates for Substantial Completion? Should the first slice expose raw milestones only?
3. Are row coverage, missing estimates and estimates by exhibit clearly separated from any broader capital program amount? Review the TBD-007 and D105C-I handling.
4. Should reconciliation require a second independent transcription of all Exhibit B amounts or documented row-by-row confirmation before publishing? Assess practical review effort and evidence requirements.
5. Does the proposed DuckDB query boundary justify Parquet for the first two snapshots? Check that cents remain exact and historical inputs can be rebuilt.

## Proposed next improvements, ordered by value and risk

1. **High value, high correctness risk.** Independently reconcile the four Exhibit B pages and classify all exact matches as comparable, held or excluded. Define evidence approval and exception reporting first.
2. **High value, moderate implementation risk.** Build a reviewed Exhibit B snapshot pair and a deterministic query for estimate and coverage changes with evidence links. Keep phases and raw source fields visible.
3. **Moderate value, high semantic risk.** Clarify milestone markers and period basis, then consider like-for-like milestone rules. Add monthly data to the analytical model only after separate owner review.

## Git and handoff

The original reviewed Stage 0 commit is `55f6e39e630c18dc5e61672965dfef4bf7b72e3c`, `feat(stage-0): establish source audit and engineering baseline`. Inspect it with `git show 55f6e39`. The corrective handoff above records the subsequent audit changes. Raw source PDFs and the virtual environment are local ignored files.

**Conditional go.** External review and owner clearance are required before Stage 1. Restrict the first implementation to the approved Exhibit B evidence and estimate-review slice.
