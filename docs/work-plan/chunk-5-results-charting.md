# Chunk 5: Full Results + Charting

**Goal:** Complete reporting, multi-backtest comparison, and interactive charts.

**Depends on:** Chunk 1 (can be built in parallel with Chunks 2-4)

## Deliverable

All result/charting methods from `api/index.md` work. Multiple backtests can be compared.

```python
import tiportfolio as ti

data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31")

p1 = ti.Portfolio("equal", [ti.Signal.Monthly(), ti.Select.All(), ti.Weigh.Equally(), ti.Action.Rebalance()], ["QQQ", "BIL", "GLD"])
p2 = ti.Portfolio("heavy_qqq", [ti.Signal.Monthly(), ti.Select.All(), ti.Weigh.Ratio(weights={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1}), ti.Action.Rebalance()], ["QQQ", "BIL", "GLD"])

# Multi-backtest comparison
result = ti.run(ti.Backtest(p1, data), ti.Backtest(p2, data))

result.summary()                  # side-by-side summary table
result.full_summary()             # all metrics
result.plot()                     # equity curves overlaid
result.plot(interactive=True)     # Plotly
result.plot_security_weights()    # weight evolution per asset
result.plot_histogram()           # return distribution

# Indexing
result[0].summary()               # first backtest only
result["equal"].summary()          # by name

# Trade records
result[0].trades                   # Trades wrapper (delegates to pd.DataFrame)
result[0].trades.sample(5)         # top-5 and bottom-5 rebalances by equity return
```

## Files to Modify

### Trades wrapper

| File | Change |
|------|--------|
| `result.py` | Add `Trades` class: wraps `pd.DataFrame` via `__getattr__` delegation. Columns: `date`, `portfolio`, `ticker`, `qty_before`, `qty_after`, `delta`, `price`, `fee`, `equity_before`, `equity_after`. Add `sample(n)` method with deduplication. |

### Full metrics

| File | Change |
|------|--------|
| `result.py` | Add `full_summary()` to `_SingleResult`: CAGR, Sharpe, Sortino, max drawdown, max drawdown duration, Calmar, monthly returns, best/worst month, win rate. Uses `config.risk_free_rate` and `config.bars_per_year`. |

### Charting

| File | Change |
|------|--------|
| `result.py` | Add `plot_security_weights()`, `plot_histogram()`. Add `interactive=True` Plotly path to `plot()`. Internal dispatch: `_render_matplotlib(data)` vs `_render_plotly(data)`. |

### Multi-backtest

| File | Change |
|------|--------|
| `result.py` | Make `BacktestResult` always a collection. `__getitem__` supports int index and string name. `ti.run(*tests)` returns `BacktestResult` wrapping `list[_SingleResult]`. `summary()` on `BacktestResult` produces side-by-side comparison table. |

## Spec Sections Covered

- Section 6: Trades wrapper, sample(n), _SingleResult, BacktestResult, summary, full_summary, plot family
- Section 6: Trade record columns, metric definitions

## Key Design Decisions (from spec)

- **BacktestResult is always a collection** — even for a single backtest. `result[0]` and `result["name"]` always work.
- **Trades.sample(n) deduplicates** — uses `~df.index.duplicated()` to handle `n >= len(r)` case where nlargest and nsmallest overlap.
- **Plotly is optional** — `interactive=True` requires plotly in the environment; `interactive=False` (default) uses Matplotlib only.
- **Metrics use config values** — `risk_free_rate` and `bars_per_year` from `TiConfig` drive Sharpe/Sortino annualisation.
