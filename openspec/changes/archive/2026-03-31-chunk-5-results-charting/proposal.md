## Why

TiPortfolio's reporting layer is minimal — basic summary metrics (total return, CAGR, max drawdown, Sharpe), a simple equity curve plot, and no trade records. Users can't inspect individual trades, view security weight evolution, see return distributions, or use interactive charts. The engine already runs complex strategies (tree portfolios, momentum, ERC), but results are opaque. Chunk 5 completes the reporting pipeline so users can analyze and present their backtests.

## What Changes

- **Trade recording**: `execute_leaf_trades` captures per-trade records (date, ticker, qty_before, qty_after, delta, price, fee, equity_before, equity_after)
- **`Trades` wrapper**: Wraps `pd.DataFrame` with `__getattr__` delegation. Adds `sample(n)` returning top-N and bottom-N rebalances by equity return, with deduplication
- **`full_summary()`**: Extends `_SingleResult` with Sortino, max drawdown duration, Calmar, monthly returns, best/worst month, win rate
- **`plot_security_weights()`**: Stacked area chart showing weight evolution per asset across rebalance dates
- **`plot_histogram()`**: Return distribution histogram
- **`plot(interactive=True)`**: Plotly dispatch for interactive equity curve charts (Plotly is optional; `interactive=False` stays Matplotlib)
- **`BacktestResult.full_summary()`**: Side-by-side full metrics for multi-backtest comparison

## Capabilities

### New Capabilities

- `trades-wrapper`: Trade record capture during execution, `Trades` class with DataFrame delegation and `sample(n)`
- `full-summary-metrics`: Extended performance metrics (Sortino, Calmar, max DD duration, monthly returns, win rate)
- `chart-enhancements`: Security weight plots, return histogram, interactive Plotly support

### Modified Capabilities

_(none — existing summary/plot behavior unchanged; new methods are additive)_

## Impact

- **Code**: `backtest.py` (trade recording in `execute_leaf_trades` + `_run_single`), `result.py` (major additions)
- **Dependencies**: plotly already in dev deps; no new runtime deps
- **Tests**: New `tests/test_result_full.py`; minor updates to `tests/test_result.py`
- **Public API**: New methods on `_SingleResult` and `BacktestResult`; new `Trades` property
