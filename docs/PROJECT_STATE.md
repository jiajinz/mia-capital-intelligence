# Project state

## Stage 0 — Ready for independent review

- Repository root was empty and isolated at intake. Git was initialized locally on `main`. The Stage 0 baseline is the commit titled `feat(stage-0): establish source audit and engineering baseline`. Resolve its exact hash with `git log -1 --format='%h %s' -- docs/REVIEW_PACKET.md` at Stage 0. This file references the commit by subject to avoid a self-referential hash.
- Python 3.13.1 and pytest 8.3.5 ran in a repository-local virtual environment. Stage 0 implements byte verification, inventory tests, and an optional read-only PDF profile.
- Three official PDFs were acquired and inventoried. The quarterly pair has same-exhibit comparison candidates, with unresolved scope and milestone questions. The September report has four reconciled financial rows in a separate series.
- The [source audit](SOURCE_AUDIT.md) records page-level controls and visually verified samples. Quarterly subtotals require a second-person amount and row-count check before publication. No independent reviewer sign-off has been recorded.
- Next checkpoint is external review of [the review packet](REVIEW_PACKET.md), then owner approval for the limited Exhibit B slice in [D004](DECISIONS.md#d004--stage-1-acceptance-criteria).
