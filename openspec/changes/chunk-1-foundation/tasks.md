> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Test Fixtures + Project Setup

- [x] 1.1 Create `tests/data/prices.csv` with 20 trading days of deterministic OHLCV data for QQQ, BIL, GLD (flat format with symbol column matching helpers output)
- [x] 1.2 Create `tests/conftest.py` with `prices_dict` fixture that loads CSV and converts to `dict[str, pd.DataFrame]` with UTC DatetimeIndex — the format all tests will use
- [x] 1.3 Verify `uv run python -m pytest` runs (even if 0 tests collected)

## 2. Core Abstractions (TDD)

- [x] 2.1 Write `tests/test_config.py` — TiConfig defaults, custom overrides, frozen dataclass
- [x] 2.2 Implement `src/tiportfolio/config.py` — TiConfig dataclass; tests pass
- [x] 2.3 Write `tests/test_algo.py` — Context construction/defaults, Algo ABC contract, AlgoQueue short-circuit and all-True
- [x] 2.4 Implement `src/tiportfolio/algo.py` — Context, Algo, AlgoQueue; tests pass
- [x] 2.5 Write `tests/test_portfolio.py` — Portfolio construction, initial state, children types, algo_queue wrapping
- [x] 2.6 Implement `src/tiportfolio/portfolio.py` — Portfolio class; tests pass

## 3. Data Layer (TDD)

- [ ] 3.1 Write `tests/test_data.py` — validate_data: aligned passes, misaligned raises, extra data check
- [ ] 3.2 Implement `validate_data` in `src/tiportfolio/data.py`; tests pass
- [ ] 3.3 Write `tests/test_data.py` — fetch_data: mock helpers, verify dict output with correct columns and UTC DatetimeIndex
- [ ] 3.4 Implement `fetch_data` in `src/tiportfolio/data.py` (wraps existing helpers, splits flat DF → per-ticker dict); tests pass

## 4. Basic Algos (TDD)

- [ ] 4.1 Write `tests/test_signal.py` — Signal.Schedule: fires on matching dates, skips others; Signal.Monthly: fires on month-end trading days only
- [ ] 4.2 Implement `src/tiportfolio/algos/signal.py` — Signal.Schedule (NYSE calendar check), Signal.Monthly (delegates to Schedule); tests pass
- [ ] 4.3 Write `tests/test_select.py` — Select.All: populates context.selected from portfolio.children
- [ ] 4.4 Implement `src/tiportfolio/algos/select.py` — Select.All; tests pass
- [ ] 4.5 Write `tests/test_weigh.py` — Weigh.Equally: equal weights for 1, 2, 3 selected items
- [ ] 4.6 Implement `src/tiportfolio/algos/weigh.py` — Weigh.Equally (long-only); tests pass
- [ ] 4.7 Write `tests/test_rebalance.py` — Action.Rebalance: calls _execute_leaf for leaf, raises RuntimeError if callback None; Action.PrintInfo: returns True, prints debug
- [ ] 4.8 Implement `src/tiportfolio/algos/rebalance.py` — Action.Rebalance, Action.PrintInfo; tests pass
- [ ] 4.9 Create `src/tiportfolio/algos/__init__.py` — re-export Signal, Select, Weigh, Action namespaces

## 5. Simulation Engine (TDD)

- [ ] 5.1 Write `tests/test_backtest.py` — mark_to_market: equity = cash + positions * price; empty portfolio = cash only
- [ ] 5.2 Write `tests/test_backtest.py` — execute_leaf_trades: first rebalance from cash, correct target qty, fee deduction, position updates
- [ ] 5.3 Write `tests/test_backtest.py` — Backtest constructor: validates data, rejects misaligned, initialises portfolio with initial_capital
- [ ] 5.4 Implement `src/tiportfolio/backtest.py` — Backtest constructor, mark_to_market, execute_leaf_trades; unit tests pass
- [ ] 5.5 Write `tests/test_backtest.py` — integration: run full 20-day backtest with fixture data, verify equity curve length and final equity against hand-calculated expected value
- [ ] 5.6 Implement simulation loop (day-by-day: mark_to_market → record_equity → evaluate_node) and `run()` function; integration test passes

## 6. Results + Public API

- [ ] 6.1 Write `tests/test_result.py` — _SingleResult: equity curve access, summary() returns DataFrame with total_return/cagr/max_drawdown/sharpe
- [ ] 6.2 Write `tests/test_result.py` — BacktestResult: collection pattern ([0], ["name"] indexing), KeyError for invalid name
- [ ] 6.3 Implement `src/tiportfolio/result.py` — _SingleResult with summary(), BacktestResult collection; tests pass
- [ ] 6.4 Implement plot() on _SingleResult — Matplotlib equity curve + drawdown subplots
- [ ] 6.5 Create `src/tiportfolio/__init__.py` — wire up public API: fetch_data, validate_data, run, Backtest, Portfolio, TiConfig, Signal, Select, Weigh, Action
- [ ] 6.6 Write end-to-end test: Quick Example code from api/index.md runs without error using fixture data (no network)
- [ ] 6.7 Run full test suite: `uv run python -m pytest` — all tests pass
