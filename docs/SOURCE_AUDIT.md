# Stage 0 source audit

## Identity and coverage

All three official candidate URLs returned HTTP 200 and PDF bytes. The [source inventory](../data/source_inventory.json) records exact byte counts, SHA-256 digests, titles, date roles, and page locations. The dates below use the memo and the Board's legislative action. The first public posting date was not established.

- **260526**, Third Quarterly Report under Directive 241354. Coverage is October 1 through December 31, 2025 (PDF p. 1). Memo March 24, 2026. Board accepted April 21, 2026. The FY 2024–2025 captions on the exhibits coexist with the explicitly printed October–December 2025 period. Preserve both. [PDF](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/260526.pdf) · [Board record](https://www.miamidade.gov/govaction/matter.asp?file=true&fileAnalysis=false&matter=260526&yearFolder=Y2026)
- **261402**, Fourth Quarterly Report under the same directive. Coverage is January 1 through March 31, 2026 (PDF p. 2). Memo August 6, 2026. Board accepted October 20, 2026. The exhibits print FY 2025–2026. The exact freeze dates of individual project-table cells remain unverified. [PDF](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261402.pdf) · [Board record](https://www.miamidade.gov/govaction/matter.asp?file=true&fileAnalysis=false&matter=261402&yearFolder=Y2026)
- **261400**, Aviation Capital Program Report labeled September 2026 (PDF pp. 1, 21–22). The catalog encodes the month as September 1–30 for indexing, without assuming an exact ledger cutoff. The memo is dated October 6, 2026. Legistar lists introduction on August 6, committee receipt on September 8, and Board acceptance on October 6. Preserve the dates in their respective roles. The monthly series has one candidate issue. [PDF](https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/261400.pdf) · [Board record](https://www.miamidade.gov/govaction/matter.asp?file=true&fileAnalysis=false&matter=261400&yearFolder=Y2026)

Page references use **one-based PDF positions**. Store a zero-based index as `position - 1` if required by a library and retain the printed labels independently. For example, monthly PDF p. 30 has `MDC030` and the exhibit's `Page 1 of 1`.

### Facilities and grain

The quarterly narrative covers MIA terminal-complex MEP, structural repairs and IT, with an IT assessment in the later report. Its Exhibit A (Reserve Maintenance Program) includes terminal systems, boarding bridges, roofs, building recertification, and explicitly unfunded or pipeline entries. Exhibit B (Capital Improvement Program) includes terminal expansions, security, baggage, garages, chiller plants, pavement, and airfield work. Rows explicitly identify MIA, OPF (e.g. AC002A), TMB (AA022A), and X51 (Y145A). Retain unknown airport for ambiguous descriptions. The exhibits do not establish full coverage of any airport or complete project spending.

The monthly narrative covers MIA and the general aviation system including OPF, TMB, X51 and Dade-Collier (PDF p. 3). Procurement (pp. 23–28 including exhibit cover) and financial reporting (pp. 29–30 including cover) use contract grain. The narrative and grant tables carry other scopes. The four financial contracts are a scoped subset, with no inferred coverage of all contracts or airports. Similar names across the quarterly and monthly series require a verified crosswalk. For example, `MDAD-CIP-V009A` appears with TMB in the monthly financial description while the procurement record's OMB description references Opa-Locka. Preserve both context fields.

## Quarterly reconciliation

The following are **audit controls**. Each subtotal sums the numeric cells headed `Total Estimated Cost` on one PDF page, in reported whole USD. The count includes every recognized project token including the placeholder and rows with missing amounts. Amount dashes are excluded from the subtotal and counted separately.

- **260526 A**. P. 8 (MDC008) 65 rows, $1,142,323,664, one dash. P. 9 (MDC009) 63 rows, $342,225,023. P. 10 (MDC010) 11 rows, $32,968,465. Total **139 rows / $1,517,517,152** in numeric cells. Pp. 9–10 show 67 explicit `NOT FUNDED` rows.
- **260526 B**. P. 11 (MDC011) 66 rows, $2,955,660,025. P. 12 (MDC012) 44 rows, $3,446,491,140. Total **110 rows / $6,402,151,165**.
- **261402 A**. P. 9 (MDC009) 67 rows, $1,662,929,736, one dash. P. 10 (MDC010) 64 rows, $443,384,902. P. 11 (MDC011) 34 rows, $82,379,382. Total **165 rows / $2,188,694,020** in numeric cells. Pp. 10–11 show 54 explicit `NOT FUNDED` rows under the pipeline heading.
- **261402 B**. P. 12 (MDC012) 68 rows, $3,356,850,420. P. 13 (MDC013) 44 rows, $3,406,481,145. Total **112 rows / $6,763,331,565**.

The line-grid and coordinate ID counts agree on all ten pages. The amount column was extracted by matching its vertical position to the ID and cross-checked with grid cells. The grid joined 29 values on 261402 A p. 10 because lines across the amount column are absent. The coordinate method and rendered table resolve that block. The grid also merges identifier and description cells for CA096A and GA025A in 261402 B p. 12. Whitespace inside older currency tokens, literal dollar signs, and wrapped descriptions require preserving cell boundaries. No quarterly exhibit grand total was located. The values above are calculated controls with visual spot checks, pending a second-person page/cell reconciliation before publication. Keep A and B separate because they overlap and may contain related scopes. A difference between full exhibit subtotals includes changes in row coverage.

### Identity and comparability

Exact tokens are unique within each document/exhibit in this sample. They overlap across reports for **137 A rows** (2 earlier-only, 28 later-only) and **107 B rows** (3 earlier-only, 5 later-only). These are candidate links.

- `D105C-I` appears in both later exhibits with the same description and $19,797,252 (pp. 9, 12). Preserve both source rows and block combined totals until reviewed.
- `CA096A` appears in earlier A p. 8 and later B p. 12, with changed description and estimate. Treat as a possible program/scope transition requiring an explicit mapping.
- `X133A` changes from Terminal D Computer Room, $2,711,000 and `NOT FUNDED` (earlier A p. 10) to Terminal D and Building 3030 Computer Room, $13,374,558 and a reported 54% (later A p. 10). `Y023A`, the earlier Building 3030 row, is absent from later A. A consolidation is a hypothesis. Exclude X133A from automatic cost comparisons.
- `TBD-007` is the printed token for a terminal-wide roof row at $525,120,616 (later A p. 9). Preserve its estimate in audit controls and withhold it from cross-period joins until identity is verified.
- `T180D` appears only in earlier B. `CA176A` gains a phase qualifier in later B and `CA176B` appears alongside it. Surface presence changes and scope questions. Retain phase suffixes and periods in IDs such as `U010F-7.1`.
- `AA017D` shows an amount dash in both periods. `W057A` has a blank performance cell and a substantial-completion `TBD` in later B p. 13. Keep the raw tokens and record explicit null reasons.

The strongest comparable field is the same labeled **Total Estimated Cost** for a reviewed, scope-consistent exact match within one exhibit. **Substantial Completion** can support tentative date comparisons after confirming milestone semantics and date status. The later **Completion Date** is a separate milestone without a counterpart in the earlier layout. Preserve suffix `A` separately. It appears on apparently actual dates, but no legend was confirmed, so withhold an automatic actual-date interpretation. Later B p. 12 reports `28-Apr-26 A` for AA005A, after the March 31 memo period end. A blanket March 31 cutoff would obscure this discrepancy. Progress columns vary from three quarter columns to one, with no confirmed periods, baseline or denominator. For example W099B has earlier 5%, 11%, 17%, then later 21% in a column headed third quarter. Report the raw values with ambiguity and withhold the delta. A numeric progress cell gives no affirmative funding classification.

### Visually verified change candidates

The top four absolute Exhibit B differences in the provisional exact-token scan were spot-checked against rendered pages. Amount comparisons below describe changes in the reported estimate and remain subject to scope verification.

- **T180B**, earlier p. 11 → later p. 12. $914,627,764 → $1,066,231,593, **+$151,603,829 (+16.58%)**. Unmarked substantial-completion entries 27-Aug-30 → 22-Nov-30, **+87 calendar days**. Ask which estimate assumptions, scope or schedule inputs changed. Later `Completion Date` is 20-Jul-31 and belongs to a different field.
- **BA061A**, earlier p. 11 → later p. 12. $345,382,437 → $466,490,921, **+$121,108,484**.
- **T072L**, earlier p. 11 → later p. 12. $257,739,575 → $362,045,963, **+$104,306,388**. Substantial completion stays 4-Feb-33, despite a separate later completion field.
- **V038A**, earlier p. 12 → later p. 13. $163,003,484 → $70,132,163, **−$92,871,321**. A decrease also merits a scope/basis check.
- **W099B**, the largest absolute A difference in the same scan, earlier p. 9 → later p. 10. $132,784,784 → $144,867,488, **+$12,082,704**. Check whether both figures cover the same phase 2 scope.

The exact-ID scan found 19 increases and 5 decreases among the 107 B pairs before semantic exclusions. These are audit observations only. A public queue needs a reviewer to confirm scope and original rows for each surfaced material finding. A funding follow-up may cite `NOT FUNDED` verbatim and ask which scope remains unfunded. There is no numeric funding gap measure in the quarterly tables.

## Monthly financial reconciliation

Compare the four Exhibit B financial rows (p. 30) to the Summary of Changes (pp. 21–22). The table is rotated. Amounts below retain source precision. Row order is prior, September, cumulative, in USD.

- `A19-MDAD-02` — 13,572,907.68 + 98,135.01 = 13,671,042.69.
- `A19-MDAD-01` — 10,996,711.29 + 96,545.62 = 11,093,256.91.
- `E20-MDAD-03` — 5,543,728.88 + 0.00 = 5,543,728.88. P. 30 prints `E20-MDAD--03`. Match manually here using description and all three expenditures.
- `MDAD-CIP-V009A` — 11,613,147.11 + 0.00 = 11,613,147.11.

Both zero September values are printed as dashes in Exhibit B and confirmed as zero dollars by the summary for the same contracts. That is evidence for these two cells only. The four row sums match all five published totals to the cent. Adopted budget $60,442,012.75, current approved budget $57,887,327.75, prior expenditures $41,726,494.96, current month $194,680.63, and cumulative $41,921,175.59. The last three totals satisfy the same identity. Audit calculation used Python `Decimal`. Source award values appear separately in Exhibit A. A difference from an adopted budget or a difference between procurement and rounded financial values requires its own analysis.

## Reproduce the audit

Download into a fresh ignored `data/raw` directory or first compare any existing local originals to the catalog. A changed digest means review the new version before replacing the manifest. These commands acquire the three approved sources on a fresh checkout.

```sh
mkdir -p data/raw
for id in 260526 261402 261400; do
  curl -fLsS --max-time 60 -o "data/raw/$id.pdf.part" \
    "https://www.miamidade.gov/govaction/legistarfiles/Matters/Y2026/$id.pdf" &&
    mv "data/raw/$id.pdf.part" "data/raw/$id.pdf" || break
done
shasum -a 256 data/raw/*.pdf
.venv/bin/python -m pip install 'pdfplumber==0.11.9'
PYTHONPATH=src .venv/bin/python scripts/profile_infrastructure.py
```

For an independent visual pass, open the pinned PDFs or render specific pages with Poppler, for example `pdftoppm -r 145 -png -f 11 -l 11 data/raw/260526.pdf tmp/pdfs/260526` after creating `tmp/pdfs`. Recount project rows, independently transcribe or double-key the amount column by row, and compare page sums and null counts above. Recheck the ranking by sorting absolute differences only after a same-exhibit, exact-token join and retain the signed differences. Verify the selected rows in both rendered pages. For the monthly reconciliation, transcribe the five financial columns on p. 30 and the three expenditure values on pp. 21–22, then sum using decimals.

If access fails, retry the listed PDF from the official legislative record in a browser and place the verified file in `data/raw`. Ask the owner to supply the official file if direct access stays blocked. Keep any unresolved source or table out of the comparison and record the failure and last verified checksum.
