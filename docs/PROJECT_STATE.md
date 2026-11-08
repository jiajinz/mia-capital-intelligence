# Project state

## Stage 0 — Conditional pass, corrective handoff

- Current branch is `main`. The independently reviewed baseline is `55f6e39e630c18dc5e61672965dfef4bf7b72e3c`, `feat(stage-0): establish source audit and engineering baseline`. This corrective unit is the commit titled `fix(audit): reject omitted and misbound Exhibit B rows`. Resolve it with `git log -1 --format='%H %s' -- scripts/profile_infrastructure.py`.
- Python 3.13.1 and pytest 8.3.5 ran in a repository-local virtual environment. Stage 0 implements byte verification, inventory tests, and an optional read-only PDF profile.
- Three official PDFs were acquired and inventoried. The quarterly pair has same-exhibit comparison candidates, with unresolved scope and milestone questions. The September report has four reconciled financial rows in a separate series.
- The owner supplied a CONDITIONAL PASS review. P1-01 was reproduced and corrected using independent 222-row Exhibit B controls, an unfiltered grid-ID check, and omission/misbinding regressions. A fresh PDFium pass and the pdfplumber profiler match all B rows. Exhibit A has exploratory controls only.
- P1-02 is accepted. The [scope review contract](SCOPE_REVIEW_CONTRACT.md) requires held-by-default pairs and evidence-bearing approval, including unchanged amounts. Executable comparison enforcement and all 107 review dispositions remain Stage 1 work. Human row-by-row sign-off and scope/basis confirmation remain open.
- P2-01's sequential acquisition example now checks the temporary file before replacement. The baseline's date-role caveats remain applicable. A pre-existing uncommitted README edit is preserved and excluded from the correction commit. Its shorter independence wording remains an owner review item.
- Next checkpoint is review of the corrected audit controls and explicit owner authorization for Stage 1. The source coverage remains the same three pinned official PDFs. This session uses the existing local bytes.
