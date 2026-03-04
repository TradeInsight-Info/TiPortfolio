# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_engine.py

# Run a single test by name
uv run pytest tests/test_engine.py::test_function_name -v

# Type checking
uv run mypy src/

# Format code
uv run black src/ tests/

# Run the CLI
uv run tiportfolio --symbols SPY QQQ GLD --weights 0.5 0.3 0.2 --start 2019-01-01 --end 2024-12-31 --rebalance month_end
```

Always use `uv run python` when running Python code.

## Architecture

The library is structured around three core concepts: **engines**, **allocation strategies**, and **schedules**.

### Data Flow

```
symbols/prices → Engine.run() → BacktestResult
                      ↓
              fetch_prices() [Alpaca → YFinance fallback]
                      ↓
              normalize_prices() → merged prices_df
                      ↓
              run_backtest() [core loop]
                      ↓
              compute_metrics() → BacktestResult
```

### Key Modules (`src/tiportfolio/`)

- **`engine.py`** — Three engine classes:
  - `BacktestEngine` (abstract base): validates OHLC data, normalizes price index, calls `run_backtest()`
  - `ScheduleBasedEngine`: fetches prices by symbol, delegates to base
  - `VolatilityBasedEngine`: adds VIX/volatility series, supports `vix_regime` schedule and `rebalance_filter` callable

- **`allocation.py`** — Allocation strategy protocol and implementations:
  - `AllocationStrategy` (Protocol): `get_symbols()` + `get_target_weights(date, total_equity, positions_dollars, prices_row, **context)`
  - `FixRatio`: static weights; weights must sum to 1.0 ±0.01
  - `VixRegimeAllocation`: switches between `high_vol_allocation` and `low_vol_allocation` based on `use_high_vol_allocation` from context
  - `VixChangeFilter`: callable that gates rebalance based on VIX delta

- **`backtest.py`** — Core simulation loop (`run_backtest()`): mark-to-market daily, rebalance on schedule dates, record `RebalanceDecision` per rebalance. Returns `BacktestResult` with equity curve, metrics, rebalance decisions.

- **`calendar.py`** — `Schedule` class wrapping valid schedule strings; `get_rebalance_dates()` maps schedule specs to NYSE trading days. Valid schedules: `month_end`, `month_start`, `month_mid`, `quarter_*`, `year_*`, `weekly_monday/wednesday/friday`, `vix_regime`, `never`.

- **`data.py`** — `fetch_prices()` tries Alpaca first (if `ALPACA_API_KEY`/`ALPACA_API_SECRET` set), falls back to YFinance. `normalize_prices()` validates and merges dict of DataFrames into a single close-price DataFrame.

- **`metrics.py`** — `compute_metrics()`: Sharpe ratio, CAGR, max drawdown, MAR ratio, Kelly leverage from daily equity series.

- **`report.py`** — `compare_strategies()`, `plot_strategy_comparison_interactive()`, `rebalance_decisions_table()` for analysis output.

- **`helpers/`** — Internal data fetching wrappers: `Alpaca` and `YFinance` classes in `helpers/data.py`. `helpers/cache.py` for diskcache. Not exported from public API.

### AllocationStrategy Protocol

Custom strategies must implement:
```python
def get_symbols(self) -> list[str]: ...
def get_target_weights(self, date, total_equity, positions_dollars, prices_row, **context) -> dict[str, float]: ...
```
Weights must sum to 1.0. The `**context` receives `vix_at_date` and `use_high_vol_allocation` when using `VolatilityBasedEngine`.

### Test Data

`tests/data/` contains local CSV files (SPY, QQQ, GLD, BIL, VIX, etc.) for offline testing. Use the `prices_three` or `prices_dict` fixtures from `conftest.py` to avoid live network calls in tests.

### Code Style

- Python 3.12 target, compatible with 3.10+
- Type annotations on all functions
- TDD: update tests first, make them fail, then update code to pass
- Keep changes simple; reuse existing utils before writing new ones
- Alert `[ALERT]` prefix when flagging potential issues

### Environment

For Alpaca data access, set `ALPACA_API_KEY` and `ALPACA_API_SECRET` (see `.env.example`). Without these, data falls back to YFinance automatically.
