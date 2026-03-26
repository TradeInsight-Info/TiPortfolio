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
result.full_summary() -> dict[str, float]
result.plot() -> None
result.plot_histogram() -> None
result.plot_security_weights() -> None
result.trades  # pd.DataFrame
```

### `summary()`

Quick overview — the most-used metrics:

| Key | Description |
|---|---|
| `start` | Backtest start date |
| `end` | Backtest end date |
| `risk_free_rate` | Risk-free rate used |
| `total_return` | Total return over the full period |
| `cagr` | Compound Annual Growth Rate |
| `daily_sharpe` | Daily Sharpe Ratio |
| `daily_sortino` | Daily Sortino Ratio |
| `max_drawdown` | Maximum Drawdown (%) |
| `calmar` | Calmar Ratio (CAGR / Max Drawdown) |
| `kelly` | Kelly Leverage |
| `final_value` | Final portfolio value |
| `total_fee` | Total fees paid |
| `rebalance_count` | Number of rebalances executed |

### `full_summary()`

Complete performance report — includes all fields from `summary()` plus:

**Period Returns**

| Key | Description |
|---|---|
| `mtd` | Month-to-date return |
| `3m` | 3-month return |
| `6m` | 6-month return |
| `ytd` | Year-to-date return |
| `1y` | 1-year return |
| `3y_ann` | 3-year annualised return |
| `5y_ann` | 5-year annualised return |
| `10y_ann` | 10-year annualised return |
| `incep_ann` | Since inception annualised return |

**Daily Statistics**

| Key | Description |
|---|---|
| `daily_mean_ann` | Daily mean return (annualised) |
| `daily_vol_ann` | Daily volatility (annualised) |
| `daily_skew` | Skewness of daily returns |
| `daily_kurt` | Excess kurtosis of daily returns |
| `best_day` | Best single-day return |
| `worst_day` | Worst single-day return |

**Monthly Statistics**

| Key | Description |
|---|---|
| `monthly_sharpe` | Monthly Sharpe Ratio |
| `monthly_sortino` | Monthly Sortino Ratio |
| `monthly_mean_ann` | Monthly mean return (annualised) |
| `monthly_vol_ann` | Monthly volatility (annualised) |
| `monthly_skew` | Skewness of monthly returns |
| `monthly_kurt` | Excess kurtosis of monthly returns |
| `best_month` | Best single-month return |
| `worst_month` | Worst single-month return |

**Yearly Statistics**

| Key | Description |
|---|---|
| `yearly_sharpe` | Yearly Sharpe Ratio |
| `yearly_sortino` | Yearly Sortino Ratio |
| `yearly_mean` | Mean annual return |
| `yearly_vol` | Annual return volatility |
| `yearly_skew` | Skewness of annual returns |
| `yearly_kurt` | Excess kurtosis of annual returns |
| `best_year` | Best single-year return |
| `worst_year` | Worst single-year return |

**Drawdown Analysis**

| Key | Description |
|---|---|
| `avg_drawdown` | Average drawdown depth |
| `avg_drawdown_days` | Average drawdown duration (days) |
| `avg_up_month` | Average positive monthly return |
| `avg_down_month` | Average negative monthly return |
| `win_year_pct` | % of calendar years with positive return |
| `win_12m_pct` | % of rolling 12-month windows with positive return |

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
