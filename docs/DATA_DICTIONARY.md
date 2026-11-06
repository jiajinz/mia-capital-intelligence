# Preliminary data dictionary

## Provenance and grain

- **Source version** — matter ID, official URL and title, SHA-256, byte count, page count, memo, introduction and acceptance dates, reporting basis, and inclusive coverage dates. Use matter ID plus checksum for version identity.
- **Source row** — source version, exhibit, section, one-based PDF position, printed labels and row locator (ordinal or bounding box). A row persists through parsing errors and duplicate detection. An ordinal follows the actual source row order and excludes headings.
- **Observation** — source row plus exact header text, raw value, normalized value, measure kind, unit, period or snapshot context, parse transformation, null reason and verification status. Retain header typos and source markers in raw evidence. Suggested review states are `extracted`, `visually_verified`, `scope_verified`, and `held_for_review`.
- **Project candidate** — quarterly directive series, exhibit and exact `Project` token, matched across documents after uniqueness and description checks. The candidate key can support a same-exhibit join. A canonical cross-exhibit project ID requires an explicit reviewer-approved mapping. Document/row identity stays distinct from the project key.
- **Contract candidate** — monthly series and exact `Contract No.` token with the reported description. Alias, OMB ID and procurement record ID are separate, evidence-bearing attributes. Preserve punctuation and review variations case by case.
- **Airport and classification** — preserve the description and source exhibit. A facility code needs direct evidence in the row or an approved mapping. Store `Department` only where reported. A project type inferred from text would need a separate derived field and documented logic.

## Quarterly observations

- **Total Estimated Cost** → `total_estimated_cost_usd`. Reported exhibit-row estimate, whole USD in these snapshots. Preserve a dash as missing. Compare across exact IDs with reviewed, equivalent scope, fiscal context and measure. Keep source exposure distinct from budget authorization, award, and spend. Do not aggregate exhibits together.
- **2nd/3rd/4th QT, % … Complete** → `performance_raw`. Column label and raw value as separate observations for each quarter column. Store a numeric percent for display with its ambiguity. A report period does not establish the quarter column's calendar mapping or progress denominator.
- **Substantial Completion** → `substantial_completion_reported`. Preserve raw date, parsed date where clear, and the independent `A` marker or `TBD`/blank reason. Hold date change rules until date status, milestone type and same scope are verified.
- **Completion Date** → `completion_date_reported`. Present in 261402. Independent milestone field. No earlier equivalent identified in these exhibits.
- **Actual completion** → separate typed value only with explicit source evidence. Preserve `A` as a raw marker until confirmed.
- **UNFUNDED PROJECTS / PROJECTS IN THE PIPELINE and NOT FUNDED** → `section_raw` plus `explicitly_unfunded` when the row says `NOT FUNDED`. Use unknown funding elsewhere. No numeric gap can be derived from the estimate alone.
- **Narrative structural/electrical ROM estimates** → `maintenance_rom_usd`. Scope-limited rough order of magnitude in the recertification discussion (260526 p. 2, 261402 p. 3). Preserve separately from exhibit estimates, and flag descriptions with `ROM` for review even when their column is labeled `Total Estimated Cost`.

## Monthly observations

- **FY 2025-2026 Adopted Budget Amount** → `adopted_fy_budget_usd`. Preserve fiscal year and published cents. No original-baseline budget series established.
- **Current Approved Budget Amount** → `current_approved_budget_usd`. Approved figure as displayed in this issue. This one report does not establish a revision history. Reserve separate fields for original and revised budgets when explicitly sourced.
- **Estimated Contract Amount / Awarded Contract Amount** → distinct procurement measures `estimated_contract_amount_usd` and `awarded_contract_amount_usd` in Exhibit A. Keep separate from Exhibit B budget and expenditure measures.
- **Prior Expenditures / Current Month Expenditures / Cumulative Expenditures to Date** → `prior_expenditures_usd`, `period_expenditures_usd`, and `cumulative_expenditures_usd`. Use exact cents. Within one reporting basis, test prior + period = cumulative for each contract and compare row sums to printed totals. A dash is missing unless another row for the same scope explicitly resolves it.
- **Estimated Completion Date / Project Phase / Comments** → preserve separately at contract grain. A comments value can qualify phase, as in the V009A row with an awarded phase and a project-closed comment.
- **Expenditures Indicator at 30%, 60%, 90%** → raw budget threshold marks. Keep distinct from progress. Validate a numeric ratio only with a verified denominator and compatible basis.

## Numeric and missing-value rules

Use Python `Decimal` for financial calculations with cents or use exact integers for the whole-dollar audit profile. The proposed SQL representation is `DECIMAL(18,2)` for amounts. Store currency and precision. Parse blanks, dashes, TBD, and labels as distinct raw states with explicit reasons. A reported zero stays a numeric zero. Preserve display precision and divide by a strictly positive earlier amount for a relative change. If the denominator is missing or zero, return no percentage. Use signed later minus earlier for dollars and elapsed calendar days between like milestones.
