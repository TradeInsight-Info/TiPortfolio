# Chunk 1: Foundation + Simplest Backtest

**Goal:** Make the Quick Example from `api/index.md` run end-to-end.

**Depends on:** Nothing — this is the starting point.

## Deliverable

This code runs and produces a chart:

```python
import tiportfolio as ti

data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31")

portfolio = ti.Portfolio(
    "monthly_rebalance",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    ["QQQ", "BIL", "GLD"],
)

result = ti.run(ti.Backtest(portfolio, data))
result.summary()
result.plot()
```

## Files to Create

### Core abstractions

| File | Contents |
|------|----------|
| `src/tiportfolio/config.py` | `TiConfig` dataclass (fee_per_share, risk_free_rate, loan_rate, stock_borrow_rate, initial_capital, bars_per_year) |
| `src/tiportfolio/algo.py` | `Context` dataclass, `Algo` ABC, `AlgoQueue` |
| `src/tiportfolio/portfolio.py` | `Portfolio` class (name, algo_queue, children, equity, cash, positions) |

### Data layer

| File | Contents |
|------|----------|
| `src/tiportfolio/data.py` | `fetch_data(tickers, start, end, source)` → `dict[str, pd.DataFrame]`; `validate_data(data, extra)` |

### Algos (leaf-only in this chunk)

| File | Contents |
|------|----------|
| `src/tiportfolio/algos/__init__.py` | Re-exports Signal, Select, Weigh, Action namespaces |
| `src/tiportfolio/algos/signal.py` | `Signal.Schedule(dates)`, `Signal.Monthly()` |
| `src/tiportfolio/algos/select.py` | `Select.All()` |
| `src/tiportfolio/algos/weigh.py` | `Weigh.Equally()` (long-only, no `short=True` yet) |
| `src/tiportfolio/algos/rebalance.py` | `Action.Rebalance()`, `Action.PrintInfo()` |

### Engine

| File | Contents |
|------|----------|
| `src/tiportfolio/backtest.py` | `Backtest` constructor, day-by-day simulation loop, `evaluate_node` (leaf path only), `execute_leaf_trades`, `mark_to_market` (leaf only), `record_equity` |

### Results

| File | Contents |
|------|----------|
| `src/tiportfolio/result.py` | `_SingleResult`, `BacktestResult` (single-backtest only), `summary()`, `plot()` (Matplotlib only, static) |

### Public API

| File | Contents |
|------|----------|
| `src/tiportfolio/__init__.py` | `fetch_data`, `validate_data`, `run`, `Backtest`, `Portfolio`, `TiConfig`, `Signal`, `Select`, `Weigh`, `Action` |

## Spec Sections Covered

- Section 1: Data layer
- Section 2: Core abstractions (Context, Algo, AlgoQueue — no Or/And/Not yet)
- Section 3: Portfolio state (leaf only)
- Section 4: Simulation engine (leaf evaluation, leaf trades, mark-to-market — no parent/child)
- Section 5: Signal.Schedule, Signal.Monthly, Select.All, Weigh.Equally, Action.Rebalance, Action.PrintInfo
- Section 6: BacktestResult basics (summary, plot — Matplotlib only)
- Section 7: TiConfig

## Out of Scope for This Chunk

- Or/And/Not branching → Chunk 2
- Signal.Quarterly, Signal.VIX → Chunks 2, 3
- Select.Momentum, Select.Filter → Chunk 2
- Weigh.Ratio, BasedOnHV, BasedOnBeta, ERC → Chunks 2, 3, 4
- Parent/child portfolio tree → Chunk 3
- Short selling, carry costs → Chunk 3
- Trades wrapper, full_summary, Plotly → Chunk 5
- Multi-backtest comparison → Chunk 5
