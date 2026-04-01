# Chunk 5.2: Update summary() and full_summary()

**Goal**: Reorder summary() metrics (Sharpe/Calmar/Sortino/MaxDD/CAGR as top 5, 3-decimal rounding) and expand full_summary() with period returns, daily/monthly/yearly statistics, and drawdown analysis sections.
**Architecture**: Modify `_SingleResult.summary()` and `_SingleResult.full_summary()` in `result.py`; all computation stays in the single result class.
**Tech Stack**: Python 3.12, pandas, numpy, math (existing dependencies only)
**Spec**: `openspec/changes/chunk-5-2-update-for-summary/specs/`

## File Map:

1. Modify : `src/tiportfolio/result.py` - Reorder summary metrics, add rounding, expand full_summary with ~40 new metrics across 4 sections
2. Modify : `tests/test_result.py` - Update metric order assertions for summary()
3. Modify : `tests/test_result_full.py` - Add tests for all new full_summary metrics (period returns, daily/monthly/yearly stats, drawdown analysis)

## Chunks

### Chunk 1: Update summary() metric ordering and rounding
Reorder the `data` dict in `summary()` so the top 5 keys are `sharpe`, `calmar`, `sortino`, `max_drawdown`, `cagr`. Round all float values to 3 decimal places.

Files:
- `src/tiportfolio/result.py` (modify `summary()` method, lines 75–136)
- `tests/test_result.py` (update `test_summary_has_key_metrics` to assert order)

Steps:
- Step 1: Reorder the `data` dict so the first 5 entries are sharpe, calmar, sortino, max_drawdown, cagr
- Step 2: Apply `round(val, 3)` to all float values before constructing the DataFrame
- Step 3: Update test assertions to verify the new metric order

### Chunk 2: Expand full_summary() with period returns
Add trailing period return calculations (mtd, 3m, 6m, ytd, 1y, 3y_ann, 5y_ann, 10y_ann, incep_ann) to full_summary().

Files:
- `src/tiportfolio/result.py` (modify `full_summary()` method, lines 138–169)
- `tests/test_result_full.py` (add tests)

Steps:
- Step 1: Compute period returns by slicing the equity curve from the appropriate lookback date to the last date
- Step 2: Annualise multi-year returns (3y, 5y, 10y) using `(end/start)^(1/years) - 1`
- Step 3: Return 0.0 or NaN for periods longer than available data
- Step 4: Add all keys to the output dict

### Chunk 3: Expand full_summary() with daily statistics
Add daily_mean_ann, daily_vol_ann, daily_skew, daily_kurt, best_day, worst_day.

Files:
- `src/tiportfolio/result.py`
- `tests/test_result_full.py`

Steps:
- Step 1: Compute daily returns from the equity curve (`pct_change().dropna()`)
- Step 2: Annualise mean and vol by multiplying by bars_per_year / sqrt(bars_per_year)
- Step 3: Compute skewness and excess kurtosis using pandas `.skew()` and `.kurt()`
- Step 4: Extract best_day and worst_day as max/min of daily returns

### Chunk 4: Expand full_summary() with monthly and yearly statistics
Add monthly_sharpe, monthly_sortino, monthly_mean_ann, monthly_vol_ann, monthly_skew, monthly_kurt, best_month, worst_month, and analogous yearly metrics.

Files:
- `src/tiportfolio/result.py`
- `tests/test_result_full.py`

Steps:
- Step 1: Resample equity curve to monthly ("ME") and yearly ("YE"), compute returns
- Step 2: Compute Sharpe/Sortino at monthly and yearly frequency
- Step 3: Compute mean, vol, skew, kurt, best, worst for each frequency
- Step 4: Annualise monthly mean/vol (×12 / ×√12)

### Chunk 5: Expand full_summary() with drawdown analysis
Add avg_drawdown, avg_drawdown_days, avg_up_month, avg_down_month, win_year_pct, win_12m_pct.

Files:
- `src/tiportfolio/result.py`
- `tests/test_result_full.py`

Steps:
- Step 1: Identify drawdown episodes (contiguous periods below cummax), compute average depth
- Step 2: Compute average drawdown duration in calendar days
- Step 3: Compute avg_up_month / avg_down_month from monthly returns
- Step 4: Compute win_year_pct from yearly returns and win_12m_pct from rolling 12-month windows
