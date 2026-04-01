## Why

The current `summary()` returns 11 metrics in an arbitrary order, and `full_summary()` only adds 4 extra metrics (max_dd_duration, best/worst month, win_rate). Users need the most decision-relevant risk/return metrics (Sharpe, Calmar, Sortino, MaxDD, CAGR) at the top, values rounded to 3 decimal places for readability, and a comprehensive `full_summary()` covering period returns, daily/monthly/yearly statistics, and drawdown analysis — the standard metrics found in professional portfolio tearsheets.

## What Changes

- **Reorder `summary()` metrics**: Sharpe, Calmar, Sortino, max_drawdown, CAGR become the first 5 rows. **BREAKING** — metric index order changes.
- **Round all float values** in `summary()` and `full_summary()` to 3 decimal places.
- **Expand `full_summary()`** with ~40 new metrics across 4 sections:
  - Period returns (mtd, 3m, 6m, ytd, 1y, 3y/5y/10y annualised, inception annualised)
  - Daily statistics (annualised mean/vol, skew, kurtosis, best/worst day)
  - Monthly statistics (Sharpe, Sortino, annualised mean/vol, skew, kurtosis, best/worst month)
  - Yearly statistics (Sharpe, Sortino, mean, vol, skew, kurtosis, best/worst year)
  - Drawdown analysis (avg drawdown, avg drawdown days, avg up/down month, win year %, win 12m %)

## Capabilities

### New Capabilities
- `period-returns`: Trailing period return calculations (mtd through inception) from the equity curve
- `frequency-statistics`: Daily, monthly, and yearly return statistics (mean, vol, skew, kurtosis, best, worst, Sharpe, Sortino)
- `drawdown-analysis`: Drawdown episode analysis (average depth, duration) and win-rate metrics

### Modified Capabilities
- `summary-metrics`: Reorder top-5 metrics and apply 3-decimal rounding to all summary/full_summary output

## Impact

- **Code**: `src/tiportfolio/result.py` — `_SingleResult.summary()` and `_SingleResult.full_summary()` methods
- **Tests**: `tests/test_result.py` and `tests/test_result_full.py` — updated assertions for metric order + new metric coverage
- **API**: `BacktestResult.summary()` / `full_summary()` — downstream consumers see new metric order and additional rows. **BREAKING** for anyone asserting on index position.
- **Dependencies**: No new dependencies — uses pandas resample, skew, kurt, numpy, and math already imported.
