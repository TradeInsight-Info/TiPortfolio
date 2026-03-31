# Chunk 5: Full Results + Charting

**Goal**: Complete reporting with trade records, full performance metrics, multi-backtest comparison, interactive Plotly charts, and security weight evolution plots.

**Architecture**: Extend `result.py` with `Trades` wrapper, `full_summary()`, and new chart methods. Modify `backtest.py` to capture trade records during `execute_leaf_trades`. Add optional Plotly dependency for `interactive=True`.

**Tech Stack**: Python 3.12, pandas, matplotlib, plotly (optional)

**Spec**: `docs/work-plan/chunk-5-results-charting.md`

## File Map

1. Modify: `src/tiportfolio/backtest.py` — Record trades in `execute_leaf_trades`, pipe trade records to `_SingleResult`
2. Modify: `src/tiportfolio/result.py` — Add `Trades` class, `full_summary()`, `plot_security_weights()`, `plot_histogram()`, Plotly dispatch in `plot()`
3. Modify: `pyproject.toml` — plotly is already an optional dev dep; verify it's available
4. Create: `tests/test_result_full.py` — Tests for full_summary, trades, new charts
5. Modify: `tests/test_result.py` — Update existing tests for any API changes

## Chunks

### Chunk A: Trade Recording + Trades Wrapper

Modify `execute_leaf_trades` to build a list of trade records (date, portfolio, ticker, qty_before, qty_after, delta, price, fee, equity_before, equity_after). Pipe records through `_run_single` to `_SingleResult`. Create `Trades` class that wraps `pd.DataFrame` with `__getattr__` delegation and `sample(n)`.

Files:
- `src/tiportfolio/backtest.py`
- `src/tiportfolio/result.py`
- `tests/test_result_full.py`

Steps:
- Add trade record capture to `execute_leaf_trades` (return list of dicts)
- Accumulate trade records in `_run_single` loop
- Pass trade records to `_SingleResult.__init__`
- Implement `Trades` class with `__getattr__` delegation to inner DataFrame
- Implement `Trades.sample(n)` with deduplication

### Chunk B: Full Summary Metrics

Add `full_summary()` to `_SingleResult` with: Sortino ratio, max drawdown duration, Calmar ratio, monthly returns, best/worst month, win rate. All use `config.risk_free_rate` and `config.bars_per_year`.

Files:
- `src/tiportfolio/result.py`
- `tests/test_result_full.py`

Steps:
- Implement Sortino ratio (downside deviation only)
- Implement max drawdown duration (bars between peak and recovery)
- Implement Calmar ratio (CAGR / |max drawdown|)
- Implement monthly returns, best/worst month, win rate
- Add `full_summary()` on `BacktestResult` for side-by-side comparison

### Chunk C: Charting Enhancements

Add `plot_security_weights()` (weight evolution per asset over time), `plot_histogram()` (return distribution). Add Plotly dispatch to `plot()` when `interactive=True`.

Files:
- `src/tiportfolio/result.py`
- `tests/test_result_full.py`

Steps:
- Implement `plot_security_weights()` using stacked area chart
- Implement `plot_histogram()` using return distribution
- Add `_render_plotly()` internal method for interactive charts
- Test that `interactive=False` returns matplotlib Figure, `interactive=True` returns plotly Figure
