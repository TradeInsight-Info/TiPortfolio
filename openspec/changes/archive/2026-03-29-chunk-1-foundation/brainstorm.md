# Chunk 1: Foundation + Simplest Backtest


**Goal**: Make the Quick Example from `api/index.md` run end-to-end — `fetch_data`, construct a Portfolio, run a Backtest, and see `summary()` + `plot()` output.
**Architecture**: Algo-stack pattern — Strategy = ordered list of `Algo` objects in an `AlgoQueue`. Four roles: Signal (when) → Select (what) → Weigh (how much) → Action (execute). Day-by-day simulation loop evaluates the tree on each bar.
**Tech Stack**: Python 3.12, pandas, yfinance, pandas-market-calendars, matplotlib, pytest (TDD)
**Spec**: `docs/superpowers/specs/2026-03-28-core-engine-implementation-design.md`

## File Map:

1. Create : `src/tiportfolio/config.py` - TiConfig dataclass with simulation parameters
2. Create : `src/tiportfolio/algo.py` - Context dataclass, Algo ABC, AlgoQueue
3. Create : `src/tiportfolio/portfolio.py` - Portfolio class with mutable state (equity, cash, positions)
4. Create : `src/tiportfolio/data.py` - fetch_data wrapper (converts existing helpers flat DF → dict), validate_data
5. Create : `src/tiportfolio/algos/__init__.py` - Re-exports Signal, Select, Weigh, Action namespaces
6. Create : `src/tiportfolio/algos/signal.py` - Signal.Schedule, Signal.Monthly
7. Create : `src/tiportfolio/algos/select.py` - Select.All
8. Create : `src/tiportfolio/algos/weigh.py` - Weigh.Equally (long-only)
9. Create : `src/tiportfolio/algos/rebalance.py` - Action.Rebalance, Action.PrintInfo
10. Create : `src/tiportfolio/backtest.py` - Backtest constructor, simulation loop, execute_leaf_trades, mark_to_market
11. Create : `src/tiportfolio/result.py` - _SingleResult, BacktestResult (collection pattern), summary(), plot()
12. Modify : `src/tiportfolio/__init__.py` - Wire up public API exports
13. Create : `tests/conftest.py` - Shared fixtures with deterministic CSV price data
14. Create : `tests/data/prices.csv` - Small deterministic price dataset for offline testing
15. Create : `tests/test_config.py` - TiConfig tests
16. Create : `tests/test_algo.py` - Context, Algo, AlgoQueue tests
17. Create : `tests/test_portfolio.py` - Portfolio construction and state tests
18. Create : `tests/test_data.py` - fetch_data and validate_data tests
19. Create : `tests/test_signal.py` - Signal.Schedule, Signal.Monthly tests
20. Create : `tests/test_select.py` - Select.All tests
21. Create : `tests/test_weigh.py` - Weigh.Equally tests
22. Create : `tests/test_rebalance.py` - Action.Rebalance, Action.PrintInfo tests
23. Create : `tests/test_backtest.py` - Simulation loop integration tests
24. Create : `tests/test_result.py` - BacktestResult, summary, plot tests


## Chunks

### Chunk A: Core Abstractions + Test Fixtures
Foundation types that everything else depends on. No simulation logic yet.

Files:
- `tests/data/prices.csv`, `tests/conftest.py` — deterministic 3-ticker price data fixture
- `src/tiportfolio/config.py` — TiConfig dataclass
- `src/tiportfolio/algo.py` — Context, Algo, AlgoQueue
- `src/tiportfolio/portfolio.py` — Portfolio class
- Tests: `test_config.py`, `test_algo.py`, `test_portfolio.py`

Steps:
- Step 1: Create CSV fixture with 20 trading days of known prices for QQQ, BIL, GLD
- Step 2: Write tests for TiConfig (defaults, custom values, frozen/immutable)
- Step 3: Implement TiConfig
- Step 4: Write tests for Context (construction, field defaults, mutable fields)
- Step 5: Write tests for Algo (ABC contract) and AlgoQueue (short-circuit, all-True, all-False)
- Step 6: Implement Context, Algo, AlgoQueue
- Step 7: Write tests for Portfolio (construction, initial state, leaf detection)
- Step 8: Implement Portfolio

### Chunk B: Data Layer
Wraps existing helpers into the `dict[str, pd.DataFrame]` API.

Files:
- `src/tiportfolio/data.py` — fetch_data, validate_data
- Tests: `test_data.py`

Steps:
- Step 1: Write tests for validate_data (aligned passes, misaligned raises ValueError, extra data)
- Step 2: Implement validate_data
- Step 3: Write tests for fetch_data (mock yfinance, verify dict output with correct columns/index)
- Step 4: Implement fetch_data (wraps existing helpers, splits flat DF → per-ticker dict, normalises DatetimeIndex to UTC)

### Chunk C: Basic Algos
Signal, Select, Weigh, Action — the four algo types needed for the Quick Example.

Files:
- `src/tiportfolio/algos/signal.py` — Signal.Schedule, Signal.Monthly
- `src/tiportfolio/algos/select.py` — Select.All
- `src/tiportfolio/algos/weigh.py` — Weigh.Equally
- `src/tiportfolio/algos/rebalance.py` — Action.Rebalance, Action.PrintInfo
- `src/tiportfolio/algos/__init__.py` — namespace re-exports
- Tests: `test_signal.py`, `test_select.py`, `test_weigh.py`, `test_rebalance.py`

Steps:
- Step 1: Write tests for Signal.Schedule (fires on correct dates, skips others)
- Step 2: Write tests for Signal.Monthly (fires on month-end trading days)
- Step 3: Implement Signal.Schedule and Signal.Monthly using pandas_market_calendars
- Step 4: Write tests for Select.All (populates context.selected from children)
- Step 5: Implement Select.All
- Step 6: Write tests for Weigh.Equally (equal weights, correct keys)
- Step 7: Implement Weigh.Equally
- Step 8: Write tests for Action.Rebalance (calls _execute_leaf for leaf nodes)
- Step 9: Implement Action.Rebalance and Action.PrintInfo

### Chunk D: Simulation Engine
The day-by-day loop that ties everything together.

Files:
- `src/tiportfolio/backtest.py` — Backtest, simulation loop, execute_leaf_trades, mark_to_market
- Tests: `test_backtest.py`

Steps:
- Step 1: Write tests for mark_to_market (leaf portfolio equity = cash + positions * price)
- Step 2: Write tests for execute_leaf_trades (correct deltas, fee deduction, position updates)
- Step 3: Write tests for Backtest constructor (validates data, initialises portfolio state)
- Step 4: Write integration test: run a full backtest with known prices, verify equity curve
- Step 5: Implement Backtest, simulation loop, execute_leaf_trades, mark_to_market, record_equity

### Chunk E: Results + Public API
BacktestResult, summary, plot, and the `__init__.py` wiring.

Files:
- `src/tiportfolio/result.py` — _SingleResult, BacktestResult, summary(), plot()
- `src/tiportfolio/__init__.py` — public API
- Tests: `test_result.py`

Steps:
- Step 1: Write tests for _SingleResult (equity curve access, summary metrics)
- Step 2: Write tests for BacktestResult (collection pattern: [0], ["name"] indexing)
- Step 3: Implement _SingleResult with summary() (total return, CAGR, max drawdown, Sharpe)
- Step 4: Implement BacktestResult collection wrapper
- Step 5: Implement plot() with Matplotlib (static equity curve + drawdown)
- Step 6: Wire up __init__.py with all public exports
- Step 7: Write end-to-end test: Quick Example code from api/index.md runs without error
