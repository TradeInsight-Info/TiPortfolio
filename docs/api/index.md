# API Reference

TiPortfolio exposes a focused public API through the `tiportfolio` package (imported as `ti`).

---

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
    ["QQQ", "BIL", "GLD"],
)

result = ti.run(ti.Backtest(portfolio, data))
result.summary()
result.plot()
```

---

## 1. Data

### `fetch_data`

```python
ti.fetch_data(
    tickers: list[str],
    start: str,                      # "YYYY-MM-DD"
    end: str,                        # "YYYY-MM-DD"
    source: str = "yfinance",        # "yfinance" | "alpaca"
) -> pd.DataFrame
```

Fetches OHLCV price data for the given tickers. Returns a DataFrame with a MultiIndex of `(date, symbol)` and columns `open`, `high`, `low`, `close`, `volume` — normalized to UTC. `context.prices` inside algos uses the same format, sliced to the current evaluation date.

---

## 2. Strategy Building

### `Portfolio`

```python
ti.Portfolio(name: str, algos: list[Algo], [str | Portfolio, ...])
```

A node in the strategy tree. The optional third argument is a list that can be:

- **omitted or empty** — portfolio with no pre-defined universe (algos manage selection entirely)
- **ticker strings** — leaf node; these are the tradeable symbols
- **`Portfolio` objects** — parent node; capital is routed to child portfolios
- **mixed** — tickers and child portfolios together

```python
ti.Portfolio("monthly", [...algos...], ["QQQ", "BIL", "GLD"])
ti.Portfolio("regime",  [...algos...], [low_vol_portfolio, high_vol_portfolio])
ti.Portfolio("dynamic", [...algos...])   # no fixed universe
```

The `algos` list is wrapped internally in an `AlgoStack`. Each algo runs in order, returning `True` to continue or `False` to abort the rebalance for this node. For tree portfolios, the parent stack runs first; if it returns `True`, the engine forks a `Context` for the selected child and evaluates it recursively.

In **parent portfolios**, `SelectAll()` populates `context.selected` with child portfolio names. `WeighEqually()` and `WeighFixedRatio()` operate on those names the same way — writing `{"long": 0.5, "short": 0.5}` to `context.weights`. Child portfolios do not need a schedule algo — the parent controls when evaluation happens.

---

### `algo` Namespace

All concrete algos live under `ti.algo.*`. A typical stack follows four roles in order:

```
Schedule → Select → Weigh → Rebalance
  When?    What?   How much?  Execute
```

#### Schedule Algos

Control *when* a rebalance is triggered. Return `False` on non-trigger dates.

`Schedule` is the primitive; `ScheduleMonthly` and `ScheduleQuarterly` are convenience wrappers that pre-configure it:

| Algo | Equivalent `Schedule` configuration |
|---|---|
| `ScheduleMonthly(day="end", next_trading_day=True)` | `Schedule(day="end", next_trading_day=True)` |
| `ScheduleMonthly(day=15, next_trading_day=True)` | `Schedule(day=15, next_trading_day=True)` |
| `ScheduleQuarterly(months=[2,5,8,11], day="end")` | `Or(Schedule(month=2), Schedule(month=5), Schedule(month=8), Schedule(month=11))` |

| Algo | Signature | Description |
|---|---|---|
| `Schedule` | `(month=None, day="end", next_trading_day=True)` | Primitive trigger — fires on `day` of `month` (or every month if `month=None`) |
| `ScheduleMonthly` | `(day="end", next_trading_day=True)` | `Schedule` preset for monthly rebalance |
| `ScheduleQuarterly` | `(months=[2,5,8,11], day="end")` | `Or`-wrapped `Schedule` preset for quarterly rebalance |

#### Select Algos

Control *which* tickers are included. Writes to `context.selected`.

| Algo | Signature | Description |
|---|---|---|
| `SelectAll` | `()` | Select all tickers |
| `SelectMomentum` | `(n, lookback, lag=1, sort_descending=True)` | Selects top/bottom `n` by momentum score |

#### Weigh Algos

Control *how much* to allocate. Reads `context.selected`, writes `context.weights`.

| Algo | Signature | Description |
|---|---|---|
| `WeighEqually` | `(sign=1)` | Equal weight; `sign=-1` for short leg |
| `WeighFixedRatio` | `(weights: dict[str, float])` | Fixed target weights |
| `WeighBasedOnHV` | `(initial_ratio, target_hv, lookback)` | Volatility-targeting weights |
| `WeighBasedOnBeta` | `(initial_ratio, target_beta, lookback)` | Beta-neutral weights |
| `WeighERC` | `(lookback, covar_method="ledoit-wolf", risk_parity_method="ccd", maximum_iterations=100, tolerance=1e-8)` | Equal Risk Contribution (Risk Parity) weights |

#### Action Algos

Execute trades or side effects.

| Algo | Signature | Description |
|---|---|---|
| `Rebalance` | `()` | Executes trades to reach target weights in `context.weights` |
| `PrintInfo` | `()` | Debug: prints current context to stdout |

#### Signal Algos

Used in parent portfolios to route between child portfolios.

| Algo | Signature | Description |
|---|---|---|
| `VixSignal` | `(high: float, low: float, signal: pd.DataFrame)` | Sets `context.selected_child` based on VIX regime; `signal` is a pre-fetched OHLCV DataFrame |
| `WeighSelected` | `(weight: float)` | Writes `{selected_child.name: weight}` to `context.weights` |

---

### `branching` Namespace

Combinators for composing algos with conditional logic. Defined in `algo.py`, re-exported through `branching.py`.

```python
ti.branching.Or(*algos: Algo)    # returns True on first algo that returns True
ti.branching.And(*algos: Algo)   # all must return True (explicit version of AlgoStack)
ti.branching.Not(algo: Algo)     # inverts result of wrapped algo
```

```python
# Trigger quarterly: month 2 OR 5 OR 8 OR 11
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

## 3. Running a Backtest

### `TiConfig`

```python
ti.TiConfig(
    fee_per_share: float = 0.0035,
    risk_free_rate: float = 0.04,
    initial_capital: float = 10_000,
    bars_per_year: int = 252,
)
```

Global defaults for all backtests. Pass a custom instance to `Backtest(config=...)` to override.

### `Backtest`

```python
ti.Backtest(
    portfolio: Portfolio,
    data: pd.DataFrame,
    fee_per_share: float | None = None,   # convenience override of TiConfig
    config: TiConfig | None = None,
)
```

Bundles a portfolio strategy with price data and configuration.

### `run`

```python
result = ti.run(*tests: Backtest) -> BacktestResult
```

Runs one or more backtests and returns a `BacktestResult` that is always collection-aware.

```python
# Single backtest
result = ti.run(ti.Backtest(portfolio, data))

# Multiple backtests — compare strategies side by side
result = ti.run(
    ti.Backtest(monthly_portfolio, data),
    ti.Backtest(quarterly_portfolio, data),
    ti.Backtest(buy_and_hold, data),
)
result.plot()           # overlaid equity curves, one line per portfolio
result.summary()        # comparison table: rows = metrics, columns = portfolio names
```

When called with multiple backtests, all `BacktestResult` methods adapt automatically:
- `summary()` / `full_summary()` return a `pd.DataFrame` (metrics × portfolios) instead of a dict
- `plot()` overlays all equity curves on a single chart
- `plot_histogram()` overlays all return distributions
- `plot_security_weights()` shows weights per portfolio in separate panels
- Individual results are accessible via `result["portfolio_name"]` or `result[0]`

`result[0]` and `result["name"]` work for **single-backtest results too**, so you can always write `result[0]` and add more backtests later without changing the rest of your code.

---

## 4. Analyzing Results

### `BacktestResult`

#### Metrics

```python
result.summary() -> dict[str, float]
result.full_summary() -> dict[str, float]
```

**`summary()`** — Quick overview of the most-used metrics:

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

**`full_summary()`** — Complete performance report. Includes all `summary()` fields plus:

*Period Returns*

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

*Daily Statistics*

| Key | Description |
|---|---|
| `daily_mean_ann` | Daily mean return (annualised) |
| `daily_vol_ann` | Daily volatility (annualised) |
| `daily_skew` | Skewness of daily returns |
| `daily_kurt` | Excess kurtosis of daily returns |
| `best_day` | Best single-day return |
| `worst_day` | Worst single-day return |

*Monthly Statistics*

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

*Yearly Statistics*

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

*Drawdown Analysis*

| Key | Description |
|---|---|
| `avg_drawdown` | Average drawdown depth |
| `avg_drawdown_days` | Average drawdown duration (days) |
| `avg_up_month` | Average positive monthly return |
| `avg_down_month` | Average negative monthly return |
| `win_year_pct` | % of calendar years with positive return |
| `win_12m_pct` | % of rolling 12-month windows with positive return |

---

#### Charts

```python
result.plot(interactive: bool = True) -> None
result.plot_histogram(interactive: bool = True) -> None
result.plot_security_weights(interactive: bool = True) -> None
```

**`plot(interactive=True)`**

Portfolio performance chart. Shows:

- Equity curve vs benchmark (default: SPY)
- Drawdown chart below

When `interactive=True`, renders with Plotly: hover to see daily return and cumulative performance, click a date to inspect the trade record for that rebalance. When `interactive=False`, renders a static Matplotlib figure suitable for export.

**`plot_histogram(interactive=True)`**

Return density chart. Shows the distribution of daily (or monthly) returns as a histogram with a KDE overlay, annotated with mean and ±1σ lines. Helps visualise skew, fat tails, and the frequency of large drawdown days.

When `interactive=True`, hover over each bucket to see exact count and return range.

**`plot_security_weights(interactive=True)`**

Asset weight chart over time. Shows a stacked area chart of each ticker's portfolio weight on every rebalance date, making allocation drift and regime shifts visually apparent.

When `interactive=True`, hover to see exact weights on any date; click a ticker in the legend to isolate it.

---

#### Trade Records

```python
result.trades  # pd.DataFrame
```

One row per rebalance event:

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

## 5. Extending TiPortfolio

### Custom Algo

Subclass `Algo` and implement `__call__`:

```python
from tiportfolio.algo import Algo, Context

class MyTrigger(Algo):
    def __call__(self, context: Context) -> bool:
        # return True to proceed, False to skip rebalance
        return context.date.month % 3 == 0
```

Then add it to any stack:

```python
ti.Portfolio("my_strategy", [MyTrigger(), ti.algo.SelectAll(), ti.algo.WeighEqually(), ti.algo.Rebalance()], [...])
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
