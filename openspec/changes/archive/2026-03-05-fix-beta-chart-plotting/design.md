# Design: Fix Beta Chart Plotting and Optimize Report Logic

## Context

**Current State:**
- `BacktestResult.plot_portfolio_beta()` fails with "Not enough overlapping dates" or returns empty charts due to:
  - Timezone mismatch between asset_curves and benchmark_prices
  - Improper index reindexing without alignment
  - Insufficient error handling for missing/misaligned data
- `BacktestResult.plot_rolling_book_composition()` has index handling issues
- `report.py` contains deprecated plotting functions (`plot_equity_curve()`, `plot_portfolio_with_assets()`) that duplicate BacktestResult methods
- 5 notebooks fail when calling beta/book composition charts

**Constraints:**
- Maintain backward compatibility where possible (deprecation vs removal)
- Existing 126 tests must pass
- Chart methods must work in both standalone scripts and Jupyter notebooks
- Support both YFinance and pre-provided benchmark data

## Goals / Non-Goals

**Goals:**
- Fix timezone alignment in `plot_portfolio_beta()` to handle tz-naive/tz-aware indices correctly
- Implement robust benchmark data fetching with automatic fallback
- Fix rolling beta calculation and ensure sufficient overlapping dates
- Fix `plot_rolling_book_composition()` index extraction and heatmap rendering
- Consolidate plotting logic — BacktestResult methods are the canonical source
- Remove unused functions from report.py or mark as deprecated
- All 5 notebooks work correctly with beta and book composition charts

**Non-Goals:**
- Change the backtest simulation logic or metrics computation
- Modify the public API beyond chart method signatures
- Implement new chart types (scope to fixing existing ones)
- Change allocation strategy interfaces

## Decisions

### 1. Timezone Handling in plot_portfolio_beta()
**Decision:** Normalize both asset and benchmark indices to tz-naive UTC before alignment.

**Rationale:** Pandas date reindexing fails silently when indices have different timezone awareness. Converting both to tz-naive ensures consistent matching.

**Alternatives Considered:**
- Keep as-is and document as user error → burden on users, breaks notebooks
- Use `reindex(..., method='nearest')` → lossy, could use wrong dates
- Localize to specific timezone → fragile if users pass different timezones

### 2. Benchmark Data Fetching Strategy
**Decision:** Cache benchmark series on instance (`_cached_benchmark`); implement two-tier fetch:
1. Use provided `benchmark_prices` if available
2. Fall back to YFinance fetch if not provided (cached after first fetch)

**Rationale:** Avoids repeated fetches in rolling calculations; respects user-provided data; gracefully handles missing symbols.

**Alternatives Considered:**
- Always fetch from YFinance → slow, fails if no internet
- Always require user to pre-fetch → inflexible, breaks ease-of-use
- Fetch inside every rolling window → wasteful, re-fetches same data

### 3. Overlapping Dates Validation
**Decision:** Before rolling beta calculation, find common dates between asset_returns and benchmark_returns. Validate length ≥ lookback_days + 1. If insufficient, raise informative ValueError with counts.

**Rationale:** Current code silently produces NaNs when dates don't align. Explicit validation with clear error messages helps users debug and adjust lookback_days or date ranges.

**Alternatives Considered:**
- Silently use what's available → confusing, produces garbage charts
- Pad with forward-fill → introduces look-ahead bias
- Reduce lookback dynamically → non-deterministic behavior

### 4. Deprecation vs Removal of report.py Functions
**Decision:**
- Audit which functions are used: check tests and imports
- If `plot_equity_curve()` and `plot_portfolio_with_assets()` are **only** in tests, remove them
- If used elsewhere, add deprecation warning and leave for one release cycle

**Rationale:** Avoid breaking existing notebooks while cleaning up API. Clear deprecation path minimizes disruption.

### 5. Rolling Book Composition Fix
**Decision:** Extract book values correctly from asset_curves; handle missing dates in rebalance_dates gracefully.

**Approach:** For each date in rebalance_dates:
- Check if date exists in asset_curves.index
- Extract values for that date
- Identify non-zero positions as "active" in that book
- Build heatmap matrix with proper row/column labels

**Rationale:** Current code loses book context; fixing ensures visualization accurately reflects state at each rebalance.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Timezone conversion edge cases** (e.g., DST boundaries) | Test with synthetic datasets including DST transitions; use pandas' `.tz_localize(None)` instead of manual conversion |
| **YFinance fetch failures** (network, symbol not found) | Wrap in try/except with clear error message; suggest pre-fetching if fetch fails repeatedly |
| **Breaking change if report.py functions are imported** | Audit codebase first; add deprecation warnings before removal; announce in release notes |
| **Performance if rolling window is very large** | Cache benchmark data to avoid re-fetch; rolling beta is O(n*lookback_days) which is acceptable for typical backtests (~250 trading days/year) |
| **Memory bloat from cached benchmark** | Only one series cached per instance; negligible for typical benchmark data (1-5 years) |

## Migration Plan

1. **Phase 1 (this change):**
   - Fix plot_portfolio_beta() with timezone and alignment logic
   - Fix plot_rolling_book_composition() index handling
   - Audit report.py; remove or deprecate unused functions
   - Update all 5 notebooks to use corrected methods
   - Add unit tests for fixed chart methods

2. **Phase 2 (future release, if deprecation warnings issued):**
   - Remove deprecated report.py functions

3. **Rollback:** If regressions found, revert commits; keep old methods in report.py until next release.

## Open Questions

1. Should `plot_portfolio_beta()` attempt to fetch benchmark for entire date range, or just the asset_curves range? → **Decision needed:** recommend asset_curves range to avoid extraneous data fetches
2. Are there use cases for `plot_equity_curve()` and `plot_portfolio_with_assets()` beyond tests? → **Action:** grep codebase + check external notebooks in examples/
3. What's the target minimum number of overlapping dates for rolling beta? → **Decision:** Use lookback_days + 1; allow users to reduce lookback_days if needed
