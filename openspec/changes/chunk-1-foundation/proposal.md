## Why

TiPortfolio has comprehensive docs and an approved spec but 0% core implementation — only data-fetching helpers exist. The library cannot be imported or used. Chunk 1 builds the minimum vertical slice so the Quick Example from `api/index.md` runs end-to-end: fetch data, construct a portfolio, run a backtest, and see results.

## What Changes

- **New** `TiConfig` dataclass — simulation parameters (fees, rates, initial capital)
- **New** `Context`, `Algo` ABC, `AlgoQueue` — the algo-stack execution model
- **New** `Portfolio` — tree node holding mutable state (equity, cash, positions)
- **New** `fetch_data` / `validate_data` — wraps existing helpers into `dict[str, pd.DataFrame]` API
- **New** Signal.Schedule, Signal.Monthly — time-based rebalance triggers
- **New** Select.All — selects all children for allocation
- **New** Weigh.Equally — equal-weight allocation (long-only)
- **New** Action.Rebalance, Action.PrintInfo — execution and debug algos
- **New** Backtest + simulation loop — day-by-day mark-to-market and leaf trade execution
- **New** BacktestResult — collection pattern with `summary()` and `plot()` (Matplotlib)
- **Modify** `__init__.py` — wire public API: `ti.fetch_data`, `ti.Portfolio`, `ti.run`, etc.

## Capabilities

### New Capabilities

- `core-abstractions`: TiConfig, Context, Algo ABC, AlgoQueue, Portfolio state management
- `data-layer`: fetch_data wrapper (flat DF → per-ticker dict), validate_data index alignment check
- `basic-algos`: Signal.Schedule, Signal.Monthly, Select.All, Weigh.Equally, Action.Rebalance, Action.PrintInfo
- `simulation-engine`: Backtest constructor, day-by-day loop, execute_leaf_trades, mark_to_market (leaf only)
- `results-basic`: _SingleResult, BacktestResult collection, summary() metrics, plot() Matplotlib

### Modified Capabilities

_(none — no existing specs to modify)_

## Impact

- **New files**: 12 source files under `src/tiportfolio/`, 10 test files under `tests/`
- **Dependencies**: All already in `pyproject.toml` (pandas, yfinance, matplotlib, pandas-market-calendars)
- **Existing code**: `helpers/` untouched — `data.py` wraps around it via composition
- **Public API surface**: Establishes the `import tiportfolio as ti` namespace used by all future chunks
