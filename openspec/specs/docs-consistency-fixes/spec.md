# Spec: docs-consistency-fixes

## Purpose

Ensure all documentation files are accurate and consistent with the current source code — correct API names, parameter names, output schemas, and no broken internal links.

## Requirements

### Requirement: index.md uses correct API
`docs/index.md` SHALL use `ti.run()` (not `run_backtest`), correct `Backtest` constructor (no `fee_per_share`), and accurate trade/summary output schemas.

#### Scenario: index.md matches current API
- **WHEN** `docs/index.md` is compared against the source code
- **THEN** all function names, parameter names, and output schemas SHALL match

### Requirement: api/index.md is accurate
`docs/api/index.md` SHALL document: `run()` with `leverage` parameter, correct parameter name `closest_trading_day`, all Signal subclasses (Monthly, Quarterly, Weekly, Yearly, Once, EveryNPeriods, VIX, Indicator), correct `summary()` keys, correct `plot()` defaults, `fetch_data` with `csv` parameter, and mention of the CLI.

#### Scenario: api/index.md covers all public API
- **WHEN** the API reference is reviewed
- **THEN** every public class, function, and parameter SHALL be accurately documented

### Requirement: api/structure.md is accurate
`docs/api/structure.md` SHALL not reference `branching.py` (doesn't exist), SHALL use `run()` (not `run_backtest`), and SHALL have correct `Context` fields.

#### Scenario: structure.md matches codebase
- **WHEN** the package structure is compared
- **THEN** all listed files and fields SHALL exist in the actual code

### Requirement: Guide docs are accurate
All guide docs SHALL use correct parameter names and values.

#### Scenario: No wrong parameter names in guides
- **WHEN** guides are reviewed
- **THEN** `closest_trading_day` SHALL be used (not `next_trading_day`), `target_hv` values SHALL be decimals (not integers), and no typos in headings

### Requirement: No broken internal links
All internal links in docs SHALL resolve to existing files.

#### Scenario: about.md links valid
- **WHEN** `mkdocs build` is run
- **THEN** no warnings about broken links in `about.md` SHALL appear
