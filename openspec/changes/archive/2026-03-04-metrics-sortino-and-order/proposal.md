## Why

The current metrics output is missing the Sortino ratio and mean excess return, two widely-used risk-adjusted metrics, and the ordering of metrics is inconsistent with industry conventions. Result comparison also surfaces all metrics, making it harder to focus on the most meaningful signals.

## What Changes

- Add `mean_excess_return` (annualized mean of daily excess returns) to `compute_metrics()`
- Add `sortino_ratio` (annualized excess return / downside deviation) to `compute_metrics()`
- Reorder metrics output: `sharpe_ratio`, `sortino_ratio`, `mar_ratio`, `cagr`, `max_drawdown`, then remaining metrics
- `BacktestResult.summary()` reflects the new order and includes the two new metrics
- Result comparison functions (`compare_strategies`) display only the top 5 metrics: `sharpe_ratio`, `sortino_ratio`, `mar_ratio`, `cagr`, `max_drawdown`

## Capabilities

### New Capabilities
- `sortino-ratio`: Compute and expose Sortino ratio and mean excess return as first-class metrics

### Modified Capabilities
- `backtest-engine`: `BacktestResult.summary()` output order and content changes (new metrics added, reordered)

## Impact

- `src/tiportfolio/metrics.py`: add two new metrics, reorder return dict
- `src/tiportfolio/backtest.py`: update `BacktestResult.summary()` to reflect new order and fields
- `src/tiportfolio/report.py`: `compare_strategies()` filters to top 5 metrics only
- Tests in `tests/test_metrics.py` and `tests/test_report.py` need updating
