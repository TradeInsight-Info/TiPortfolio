
# TiPortfolio

TiPortfolio is a portfolio management tool with built-in portfolio optimization algorithms for backtesting trading strategies. It supports different allocation strategies, rebalancing schedules, and volatility-based engines.

## Commands

```bash
uv sync                        # install all dependencies
uv run pytest                  # run all tests
uv run pytest tests/file.py -v # run single file
uv run pytest -k "pattern"     # run matching tests
uv run mypy src/               # type check
uv run black src/ tests/       # format
uv run python                  # always use uv run python, not python directly
```

## Project Architecture

Three core concepts:

1. **Engines** (`engine/`): `BacktestEngine` (base), `ScheduleBasedEngine`, `VolatilityBasedEngine`
2. **Allocation Strategies** (`allocation/`): `FixRatio`, `VixRegimeAllocation`, `VolatilityTargeting`, `DollarNeutral`, `BetaNeutral`
3. **Schedules** (`calendar.py`): control rebalancing frequency

### Key Modules (`src/tiportfolio/`)

- **`engine/`** — `BacktestEngine` (validates OHLC, normalizes index), `ScheduleBasedEngine` (fetches by symbol), `VolatilityBasedEngine` (adds VIX series, supports `vix_regime` schedule and `rebalance_filter`)
- **`allocation/`** — `AllocationStrategy` (ABC); `FixRatio` (static weights); `VixRegimeAllocation` (high/low vol switching via `use_high_vol_allocation` context); `VolatilityTargeting`, `DollarNeutral`, `BetaNeutral`
- **`backtest.py`** — `run_backtest()`: daily mark-to-market, rebalance on schedule dates, returns `BacktestResult` (equity curve, metrics, rebalance decisions)
- **`calendar.py`** — `Schedule`; valid values: `month_end`, `month_start`, `month_mid`, `quarter_*`, `year_*`, `weekly_monday/wednesday/friday`, `vix_regime`, `never`
- **`data.py`** — `fetch_prices()` (Alpaca → YFinance fallback); `normalize_prices()` (merges to close-price DataFrame)
- **`metrics.py`** — `compute_metrics()`: Sharpe, CAGR, max drawdown, MAR, Kelly
- **`report.py`** — `compare_strategies()`, `plot_strategy_comparison_interactive()`, `rebalance_decisions_table()`
- **`helpers/`** — Internal: `Alpaca`/`YFinance` wrappers, `cache.py`; not public API

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

### AllocationStrategy ABC

Custom strategies inherit from `AllocationStrategy` and implement:

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

Weights must sum to 1.0. `**context` passes `vix_at_date` and `use_high_vol_allocation` when using `VolatilityBasedEngine`.

## Environment Variables

- `ALPACA_API_KEY` / `ALPACA_API_SECRET`: optional; falls back to YFinance without them

## Conventions

- Use `[ALERT]` prefix when flagging potential issues
