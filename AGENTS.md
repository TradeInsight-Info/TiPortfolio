# AGENTS.md

This file provides guidance for AI agents working with the TiPortfolio codebase.

## Project Overview

TiPortfolio is a portfolio management tool with built-in portfolio optimization algorithms for backtesting trading strategies. It supports different allocation strategies, rebalancing schedules, and volatility-based engines.

## Build, Lint, and Test Commands

### Installation

```bash
# Install all dependencies (including dev)
uv sync

# Install with dev dependencies
uv sync --group dev
```

### Testing

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_engine.py

# Run a single test by name
uv run pytest tests/test_engine.py::test_function_name -v

# Run tests with verbose output
uv run pytest -v

# Run tests matching a pattern
uv run pytest -k "test_name_pattern"
```

### Type Checking

```bash
# Run mypy type checker on source
uv run mypy src/
```

### Code Formatting

```bash
# Format code with black
uv run black src/ tests/
```

### Running the CLI

```bash
# Run the CLI tool
uv run tiportfolio --symbols SPY QQQ GLD --weights 0.5 0.3 0.2 --start 2019-01-01 --end 2024-12-31 --rebalance month_end
```

### Python Execution

Always use `uv run python` when running Python code directly, not just `python`.

## Code Style Guidelines

### General Principles

- **Python 3.12 target**, compatible with 3.10+
- **Simplicity first**: If a single file can encapsulate functionality without compromising clarity, prefer that approach. Avoid fancy class structures unless necessary.
- **TDD approach**: Write/update tests first, make them fail, then implement code to pass.
- **Keep changes simple**: Reuse existing utilities before writing new ones.

### Type Annotations

- All functions must have **type annotations** on parameters and return types
- Use Python's built-in types (e.g., `list[str]`, `dict[str, float]`)
- Use `Any` from typing when type cannot be precisely specified

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `BacktestEngine`, `FixRatio`)
- **Functions/methods**: `snake_case` (e.g., `get_symbols`, `run_backtest`)
- **Constants**: `UPPER_SNAKE_CASE`
- **Modules**: `snake_case`
- **Private methods**: using `_` prefix (e.g., `_internal_method`)

### Imports

- Use **absolute imports** from package root
- Group imports in this order: standard library, third-party, local
- Sort imports alphabetically within each group
- Example:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import pandas as pd

from tiportfolio.calendar import Schedule
from tiportfolio.metrics import compute_metrics
```

### Docstrings

- Use **Google-style** docstrings for public APIs
- Include Args, Returns, Raises sections when applicable
- Keep docstrings concise but informative

### Error Handling

- Use **custom exceptions** sparingly; prefer built-in ones
- Validate inputs early with descriptive error messages
- Use `ValueError` for invalid arguments, `TypeError` for wrong types

### Data Classes

- Use `@dataclass` decorator for simple data containers
- Implement `__post_init__` for validation
- Example:

```python
@dataclass
class FixRatio:
    weights: dict[str, float]

    def __post_init__(self) -> None:
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"weights must sum to 1.0; got sum={total}")
```

### Protocols

- Use `Protocol` from typing for duck-typing interfaces
- Name protocols with `Strategy` suffix (e.g., `AllocationStrategy`)

### Testing Conventions

- Test files: `test_<module>.py` or `test_<feature>.py`
- Test data: Use fixtures from `conftest.py` to avoid network calls
- Use local CSV files in `tests/data/` for offline testing
- Test fixtures: `prices_three`, `prices_dict` from `conftest.py`

### Project Architecture

The library has three core concepts:

1. **Engines** (`engine.py`): `BacktestEngine`, `ScheduleBasedEngine`, `VolatilityBasedEngine`
2. **Allocation Strategies** (`allocation.py`): `FixRatio`, `VixRegimeAllocation`, `VixChangeFilter`
3. **Schedules** (`calendar.py`): Control rebalancing frequency

#### Key Modules (`src/tiportfolio/`)

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

### AllocationStrategy Protocol

Custom strategies must implement:

```python
def get_symbols(self) -> list[str]: ...
def get_target_weights(
    self,
    date: pd.Timestamp,
    total_equity: float,
    positions_dollars: dict[str, float],
    prices_row: pd.Series,
    **context: Any,
) -> dict[str, float]: ...
```

Weights must sum to 1.0. The `**context` receives `vix_at_date` and `use_high_vol_allocation` when using `VolatilityBasedEngine`.

### Environment Variables

- `ALPACA_API_KEY` and `ALPACA_API_SECRET`: For Alpaca data (optional)
- Without these, data automatically falls back to YFinance

### Alert Prefix

Use `[ALERT]` prefix when flagging potential issues or areas requiring attention.

### Testing Data

- `tests/data/` contains local CSV files (SPY, QQQ, GLD, BIL, VIX, etc.) for offline testing
- Use fixtures from `conftest.py` to avoid live network calls in tests
