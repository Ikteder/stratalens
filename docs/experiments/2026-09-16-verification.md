# Verification record: 2026-09-16

## Environment

- Local date: 2026-09-16 America/Denver
- Selection and analysis seed: `20260916`
- Runtime: Python standard library; exact runtime version recorded in the final run log

## Synthetic fixture result

Input: `examples/checkout_demo.csv`
Rows: 2,000
Comparable strata: 3 of 3

| Metric | Result |
|---|---:|
| Aggregate control rate | 46.00% |
| Aggregate treated rate | 26.00% |
| Aggregate effect | -20.00 percentage points |
| Standardized control rate | 33.50% |
| Standardized treated rate | 38.50% |
| Standardized effect | +5.00 percentage points |
| Composition gap | -25.00 percentage points |
| Largest group-share gap | 50.00 percentage points |
| Classification | `strong_reversal` |

The 1,000 requested bootstrap replicates all produced valid overlap comparisons. Percentile intervals were:

| Quantity | 95% interval |
|---|---|
| Aggregate effect | [-24.0017%, -15.9231%] |
| Standardized effect | [+0.2221%, +9.2071%] |
| Composition gap | [-28.2212%, -21.6068%] |

## Checks

- Python compilation: passed.
- Unit tests: 11/11 passed before and after the documentation pass on Python 3.14.7.
- Successful CLI contract: exit 0 and all three output files written.
- Invalid-input CLI contract: exit 2 with a field-specific message.
- Isolated editable install and dependency check: passed with no broken requirements.
- Source distribution and wheel build: passed. The initial metadata form produced a deprecation warning, so the license was updated to the SPDX string `MIT` before the final build.
- README em dash count: 0.
- SVG XML parse: passed.
- Browser QA: Microsoft Edge through Playwright rendered the standalone report at 1280 by 900 and 390 by 844. At both sizes, document scroll width equaled client width, 7 cards and 3 stratum rows were present, and captured console warnings/errors were 0. The narrow cards stacked cleanly and the wide evidence table remained in its own scroll container.
- Hosted CI boundary: an intended Python 3.10/3.12/3.14 workflow passed local syntax review, but GitHub rejected its publication because the saved OAuth credential lacks `workflow` scope and no SSH key is configured. The workflow and CI claims were removed before publication. Local Python 3.14.7 results remain the verified boundary.
- Public repository: `https://github.com/Ikteder/stratalens`, visibility `public`, default branch `main`.
- Public rendering check: the repository page returned HTTP 200 and `docs/assets/demo-overview.svg` returned HTTP 200 as `image/svg+xml`.
- Git verification: the publication commit matched remote `main`; the final evidence commit and SHA were verified after this record was updated.

## Interpretation

These numbers verify calculations against an intentionally constructed synthetic fixture. They are not estimates of a real checkout treatment and do not validate causal identification.
