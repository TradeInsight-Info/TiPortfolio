# API Reference

TiPortfolio exposes a focused public API through the `tiportfolio` package (imported as `ti`).

## Quick Example

```python
import tiportfolio as ti

data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31")

portfolio = ti.Portfolio(
    "monthly_rebalance",
    [
        ti.algo.ScheduleMonthly(),
        ti.algo.SelectAll(),
        ti.algo.WeighEqually(),
        ti.algo.Rebalance(),
    ],
    children=["QQQ", "BIL", "GLD"],
)

result = ti.run_backtest(ti.Backtest(portfolio, data))
result.summary()
result.plot()
```

---

## `fetch_data`

```python
ti.fetch_data(
    tickers: list[str],
    start: str,           # "YYYY-MM-DD"
    end: str,             # "YYYY-MM-DD"
    source: str = "yfinance",   # "yfinance" | "alpaca"
) -> pd.DataFrame
```

Fetches OHLCV price data for the given tickers. Returns a DataFrame with a MultiIndex of `(date, symbol)` normalized to UTC.

---

## `Portfolio`

```python
ti.Portfolio(
    name: str,
    algos: list[Algo],
    children: list[str | Portfolio],
)
```

A portfolio node in the strategy tree. `children` accepts either ticker strings (leaf nodes) or nested `Portfolio` objects (sub-strategies). Both are children in the same tree — a leaf portfolio's children are its tradeable symbols.

```python
# Leaf portfolio — children are ticker strings
ti.Portfolio("monthly", [...algos...], children=["QQQ", "BIL", "GLD"])

# Parent portfolio — children are sub-portfolios (regime switching)
ti.Portfolio("regime", [...algos...], children=[low_vol_portfolio, high_vol_portfolio])
```

The `algos` list is internally wrapped in an `AlgoStack` — each algo runs in order and returns `True` to continue or `False` to abort the rebalance for this node.

For tree portfolios, the parent's algos run first. A signal algo sets `context.selected_child`, then `WeighSelected` records the weight. The engine then evaluates the selected child's full algo stack with a forked context. If the parent returns `False`, the subtree is skipped entirely.

---

## `Backtest`

```python
ti.Backtest(
    portfolio: Portfolio,
    data: pd.DataFrame,
    fee_per_share: float | None = None,
    config: TiConfig | None = None,
)
```

Bundles a portfolio strategy with price data and configuration. `fee_per_share` overrides `TiConfig.fee_per_share` for convenience.

---

## `run_backtest`

```python
result = ti.run_backtest(test: Backtest) -> BacktestResult
```

Runs the backtest simulation. Iterates over trading days, evaluates the portfolio tree on each date, and executes rebalance trades when triggered.

---

## `BacktestResult`

```python
result.summary() -> dict[str, float]
result.plot() -> None
result.plot_histogram() -> None
result.plot_security_weights() -> None
result.trades  # pd.DataFrame
```

### `summary()`

Returns a dict with these keys:

| Key | Description |
|---|---|
| `sharpe` | Sharpe Ratio |
| `sortino` | Sortino Ratio |
| `mar` | MAR Ratio (CAGR / Max Drawdown) |
| `cagr` | Compound Annual Growth Rate |
| `max_drawdown` | Maximum Drawdown (%) |
| `kelly` | Kelly Leverage |
| `mean_excess_return` | Mean return above risk-free rate |
| `final_value` | Final portfolio value |
| `total_fee` | Total fees paid |
| `rebalance_count` | Number of rebalances executed |

### `trades` DataFrame

One row per rebalance event. Columns:

| Column | Description |
|---|---|
| `date` | Rebalance date |
| `equity_before` | Portfolio value before trades |
| `equity_after` | Portfolio value after trades |
| `fee_paid` | Total fee for this rebalance |
| `{TICKER}_price` | Price at execution |
| `{TICKER}_qty_before` | Shares held before |
| `{TICKER}_trade_qty` | Shares bought (+) or sold (−) |
| `{TICKER}_qty_after` | Shares held after |
| `{TICKER}_value_after` | Position value after |

---

## `TiConfig`

```python
ti.TiConfig(
    fee_per_share: float = 0.0035,
    risk_free_rate: float = 0.04,
    initial_capital: float = 10_000,
    bars_per_year: int = 252,
    benchmark: str = "SPY",
)
```

Global defaults for all backtests. Pass a custom instance to `Backtest(config=...)` to override.

---

## `algo` Namespace

All concrete algos live under `ti.algo.*`.

### Schedule Algos

Control *when* a rebalance is triggered. Return `False` (skip) on non-trigger dates.

| Algo | Signature | Description |
|---|---|---|
| `ScheduleMonthly` | `(day="end", next_trading_day=True)` | Triggers at month-end or a specific day |
| `ScheduleQuarterly` | `(months=[2,5,8,11], day=15)` | Triggers on specific months |
| `Schedule` | `(month=None, day="end", next_trading_day=True)` | Generic fixed-time trigger |

### Select Algos

Control *which* tickers are included in the rebalance. Writes to `context.selected`.

| Algo | Signature | Description |
|---|---|---|
| `SelectAll` | `()` | Selects the full universe |
| `SelectMomentum` | `(n, lookback, lag=1, sort_descending=True)` | Selects top/bottom `n` by momentum score |

### Weigh Algos

Control *how much* to allocate to each selected ticker. Writes target weights to `context.weights`.

| Algo | Signature | Description |
|---|---|---|
| `WeighEqually` | `(sign=1)` | Equal weight; `sign=-1` for short leg |
| `WeighFixedRatio` | `(weights: dict[str, float])` | Fixed target weights |
| `WeighBasedOnHV` | `(initial_ratio, target_hv, lookback)` | Volatility-targeting weights |
| `WeighBasedOnBeta` | `(initial_ratio, target_beta, lookback)` | Beta-neutral weights |

### Action Algos

Execute trades or side effects.

| Algo | Signature | Description |
|---|---|---|
| `Rebalance` | `()` | Executes trades to reach target weights |
| `PrintInfo` | `()` | Debug: prints current context to stdout |

### Signal Algos

Used in tree-structured portfolios to route between child portfolios.

| Algo | Signature | Description |
|---|---|---|
| `VixSignal` | `(high: float, low: float, signal: pd.DataFrame)` | Selects child portfolio based on VIX regime; `signal` is a pre-fetched OHLCV DataFrame for VIX |
| `WeighSelected` | `(weight: float)` | Assigns weight to `context.selected_child` in `context.weights` |

---

## `branching` Namespace

Combinators for composing algos with conditional logic. `Or`, `And`, and `Not` are defined in `algo.py` and re-exported through `branching.py`, making `ti.branching` a distinct namespace while keeping the implementation in one place.

```python
ti.branching.Or(*algos: Algo)    # runs branches in order; returns True on first True
ti.branching.And(*algos: Algo)   # explicit AND; all must return True (same as AlgoStack)
ti.branching.Not(algo: Algo)     # inverts result of wrapped algo
```

`AlgoStack` is implicit `And` — use explicit `And` when nesting inside `Or` or `Not`:

```python
# Trigger on month 2 OR month 5 OR month 8 OR month 11
ti.branching.Or(
    ti.algo.Schedule(month=2),
    ti.algo.Schedule(month=5),
    ti.algo.Schedule(month=8),
    ti.algo.Schedule(month=11),
)

# Trigger only when NOT in high-volatility regime
ti.branching.Not(ti.algo.VixSignal(high=30, low=20, signal=vix_data))
```

---

## Extending TiPortfolio

### Custom Algo

Subclass `Algo` and implement `__call__`:

```python
from tiportfolio.algo import Algo, Context

class MyTrigger(Algo):
    def __call__(self, context: Context) -> bool:
        # return True to proceed, False to skip rebalance
        return context.date.month % 3 == 0
```

### Custom Data Source

Subclass `helpers.data.DataSource` and implement `_fetch()`:

```python
from tiportfolio.helpers.data import DataSource
import pandas as pd

class MyDataSource(DataSource):
    def _fetch(self, symbols: list[str], start: str, end: str) -> pd.DataFrame:
        ...
```
