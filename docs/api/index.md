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

---

## 1. Data

### `fetch_data`

```python
ti.fetch_data(
    tickers: list[str],
    start: str,                      # "YYYY-MM-DD"
    end: str,                        # "YYYY-MM-DD"
    source: str = "yfinance",        # "yfinance" | "alpaca"
) -> dict[str, pd.DataFrame]
```

Fetches OHLCV price data for the given tickers. Returns a `dict` keyed by ticker string. Each value is a `pd.DataFrame` with a `DatetimeIndex` (UTC) and columns `open`, `high`, `low`, `close`, `volume`.

`context.prices` inside algos is this same dict — the **full history** for all tickers, not sliced. Algos slice to their own lookback window using `context.prices[ticker].loc[start:end]`.

### `validate_data`

```python
ti.validate_data(
    data: dict[str, pd.DataFrame],
    extra: dict[str, pd.DataFrame] | None = None,
) -> None
```

Validates that all DataFrames in `data` (and optionally `extra`) share identical `DatetimeIndex` values. Raises `ValueError` with the first misaligned date and the ticker names involved. Called automatically at `Backtest` construction; also callable explicitly before running.

---

## 2. Strategy Building

### `Portfolio`

```python
ti.Portfolio(
    name: str,
    algos: list[Algo],
    children: list[str] | list[Portfolio] | list[str | Portfolio] | None = None,
)
```

A node in the strategy tree. `children` is optional (`None` by default) and accepts:

- `None` — no pre-defined universe; algos manage selection entirely
- `list[str]` — leaf node; tradeable ticker symbols
- `list[Portfolio]` — parent node; capital is routed to child portfolios
- `list[str | Portfolio]` — mixed tickers and child portfolios

```python
ti.Portfolio("monthly", [...algos...], ["QQQ", "BIL", "GLD"])
ti.Portfolio("regime",  [...algos...], [low_vol_portfolio, high_vol_portfolio])
ti.Portfolio("dynamic", [...algos...])   # no children
```

The `algos` list is wrapped internally in an `AlgoQueue`. Each algo runs in order, returning `True` to continue or `False` to abort the rebalance for this node. For tree portfolios, the parent's `AlgoQueue` runs first; if it returns `True`, the engine forks a `Context` for the selected child and evaluates it recursively.

In **parent portfolios**, `Select.All()` populates `context.selected` with child portfolio names. `Weigh.Equally()` and `Weigh.Ratio()` operate on those names the same way — writing `{"long": 0.5, "short": 0.5}` to `context.weights`. Child portfolios do not need a schedule algo — the parent controls when evaluation happens.

---

### Algo Namespaces

All algo namespaces are exposed directly under `ti`. A typical stack follows four roles in order:

```
Signal.*  → Select.*  → Weigh.*  → Action.*
  When?      What?     How much?   Execute
```

#### Signal Algos

Control *when* and *which branch* the queue proceeds through. All signal algos return `False` to halt the queue when their condition is not met.

Signal algos fall into two sub-types:

**Time-based signals** — fire on a calendar schedule:

`Signal` is a namespace. `Signal.Schedule` is the primitive; `Signal.Monthly` and `Signal.Quarterly` are proxy subclasses that call `Signal.Schedule` with preset configuration:

| Algo | Equivalent `Signal.Schedule` configuration |
|---|---|
| `Signal.Monthly(day="end", next_trading_day=True)` | `Signal.Schedule(day="end", next_trading_day=True)` |
| `Signal.Monthly(day=15, next_trading_day=True)` | `Signal.Schedule(day=15, next_trading_day=True)` |
| `Signal.Quarterly(months=[2,5,8,11], day="end")` | `Or(Signal.Schedule(month=2), ..., Signal.Schedule(month=11))` |

| Algo | Signature | Description |
|---|---|---|
| `Signal.Schedule` | `(month=None, day="end", next_trading_day=True)` | Base — fires on `day` of `month` (or every month if `month=None`) |
| `Signal.Monthly` | `(day="end", next_trading_day=True)` | Proxy: monthly rebalance preset |
| `Signal.Quarterly` | `(months=[2,5,8,11], day="end")` | Proxy: `Or`-wrapped quarterly rebalance preset |

**Market-based signals** — fire based on market data; used in parent portfolios to route capital to child portfolios:

| Algo | Signature | Description |
|---|---|---|
| `Signal.VIX` | `(high: float, low: float, data: dict[str, pd.DataFrame])` | Writes the active child portfolio to `context.selected` and `{child.name: 1.0}` to `context.weights` based on VIX regime. `data` must contain `"^VIX"`. **Children ordering:** `children[0]` = low-vol regime (VIX < `low`), `children[1]` = high-vol regime (VIX > `high`). Between thresholds, previous regime persists (hysteresis). |

#### Select Algos

Control *which* tickers are included. Writes to `context.selected`.

`Select` is a namespace. `Select.All` is the standard selector; `Select.Momentum` is a direct implementation that computes momentum scores and writes the selected tickers to `context.selected`:

| Algo | Signature | Description |
|---|---|---|
| `Select.All` | `()` | Selects all tickers in the portfolio |
| `Select.Momentum` | `(n: int, lookback: pd.DateOffset, lag: pd.DateOffset = pd.DateOffset(days=1), sort_descending: bool = True)` | Selects top/bottom `n` tickers by momentum score; writes to `context.selected` |
| `Select.Filter` | `(data: dict[str, pd.DataFrame], condition: Callable[[dict[str, pd.Series]], bool])` | Boolean gate — returns `False` to halt the queue (no rebalance) if `condition` fails; returns `True` without modifying `context.selected` if it passes |

#### Weigh Algos

Control *how much* to allocate. Reads `context.selected`, writes `context.weights`.

`Weigh` is a namespace. `Weigh.Ratio` accepts an explicit weights dict; all other variants compute their specific scheme and write to `context.weights`:

| Algo | Signature | Description |
|---|---|---|
| `Weigh.Equally` | `(short: bool = False)` | Divides capital equally across `context.selected`; `short=True` for short leg |
| `Weigh.Ratio` | `(weights: dict[str, float])` | Applies provided weights (normalised so absolute values sum to 1; handles short positions) |
| `Weigh.BasedOnHV` | `(initial_ratio: dict[str, float], target_hv: float, lookback: pd.DateOffset)` | Volatility-targeting weights; `target_hv` is an annualised decimal (e.g. `0.15` = 15% vol) |
| `Weigh.BasedOnBeta` | `(initial_ratio: dict[str, float], target_beta: float, lookback: pd.DateOffset, base_data: pd.DataFrame)` | Beta-neutral weights; `base_data` is the benchmark OHLCV DataFrame (e.g. SPY) |
| `Weigh.ERC` | `(lookback: pd.DateOffset, covar_method: str = "ledoit-wolf", risk_parity_method: str = "ccd", maximum_iterations: int = 100, tolerance: float = 1e-8)` | Equal Risk Contribution (Risk Parity) weights |

#### Action Algos

Execute trades or side effects. All live under the `Action` namespace:

| Algo | Signature | Description |
|---|---|---|
| `Action.Rebalance` | `()` | Executes trades to reach target weights in `context.weights` |
| `Action.PrintInfo` | `()` | Debug: prints current context to stdout |

---

### `AlgoQueue`

`AlgoQueue` is the internal container that runs a portfolio's algo list. The name reflects its semantics: algos are processed **in order from the top**, like a queue — the first algo runs first, the second runs second, and so on. This is distinct from a "stack" (which implies LIFO/last-in-first-out). `Portfolio` wraps the `algos` list in an `AlgoQueue` automatically.

`And` in the `branching` namespace is an explicit, nestable version of `AlgoQueue` for use inside `Or` or `Not`.

---

### Branching Combinators

Combinators for composing algos with conditional logic. Defined in `algo.py`, exported directly on the `ti` namespace.

```python
ti.Or(*algos: Algo)    # returns True on first algo that returns True
ti.And(*algos: Algo)   # all must return True (explicit version of AlgoQueue)
ti.Not(algo: Algo)     # inverts result of wrapped algo
```

```python
# Trigger quarterly: month 2 OR 5 OR 8 OR 11
ti.Or(
    ti.Signal.Schedule(month=2),
    ti.Signal.Schedule(month=5),
    ti.Signal.Schedule(month=8),
    ti.Signal.Schedule(month=11),
)

# Trigger only when NOT in high-volatility regime
ti.Not(ti.Signal.VIX(high=30, low=20, data=vix_data))
```

---

## 3. Running a Backtest

### `TiConfig`

```python
ti.TiConfig(
    fee_per_share: float = 0.0035,
    risk_free_rate: float = 0.04,
    loan_rate: float = 0.0514,        # borrowing cost for leveraged positions
    stock_borrow_rate: float = 0.07,  # short-selling borrow fee; varies by security
    initial_capital: float = 10_000,
    bars_per_year: int = 252,
)
```

Global defaults for all backtests. Pass a custom instance to `Backtest(config=...)` to override.

### `Backtest`

```python
ti.Backtest(
    portfolio: Portfolio,
    data: dict[str, pd.DataFrame],        # same dict returned by fetch_data
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
- `summary()` / `full_summary()` return a `pd.DataFrame` with one column per portfolio
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
result.summary() -> pd.DataFrame
result.full_summary() -> pd.DataFrame
```

Both always return a `pd.DataFrame` — rows are metric names, columns are portfolio names. For a single backtest there is one column; for multiple backtests each portfolio gets its own column, enabling direct side-by-side comparison with `result.summary()["portfolio_name"]`.

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

- Equity curve
- Drawdown chart below

When `interactive=True`, renders with Plotly: hover to see daily return and cumulative performance. When `interactive=False`, renders a static Matplotlib figure suitable for export.

**`plot_histogram(interactive=True)`**

Return density chart. Shows the distribution of daily (or monthly) returns as a histogram with a KDE overlay, annotated with mean and ±1σ lines. Helps visualise skew, fat tails, and the frequency of large drawdown days.

When `interactive=True`, hover over each bucket to see exact count and return range.

**`plot_security_weights(interactive=True)`**

Asset weight chart over time. Shows a stacked area chart of each ticker's portfolio weight on every rebalance date, making allocation drift and regime shifts visually apparent.

When `interactive=True`, hover to see exact weights on any date; click a ticker in the legend to isolate it.

---

#### Trade Records

```python
result.trades  # Trades — a pd.DataFrame wrapper
```

One row per rebalance event. Negative `qty` values indicate short positions.

| Column | Description |
|---|---|
| `date` | Rebalance date |
| `equity_before` | Portfolio value before trades |
| `equity_after` | Portfolio value after trades |
| `fee_paid` | Total fee for this rebalance |
| `{TICKER}_price` | Price at execution |
| `{TICKER}_qty_before` | Shares held before (negative = short) |
| `{TICKER}_trade_qty` | Shares bought (+) or sold/shorted (−) |
| `{TICKER}_qty_after` | Shares held after (negative = short) |
| `{TICKER}_value_after` | Position value after (negative for short) |

`result.trades` supports all standard `pd.DataFrame` operations and adds one method:

```python
result.trades.sample(n: int) -> pd.DataFrame
```

Returns the top `n` and bottom `n` rebalances ranked by equity return (`equity_after / equity_before - 1`). Useful for spotting the best and worst rebalance decisions during debugging. Returns at most `2n` rows; gracefully returns fewer if fewer than `n` rebalances exist.

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
ti.Portfolio("my_strategy", [MyTrigger(), ti.Select.All(), ti.Weigh.Equally(), ti.Action.Rebalance()], [...])
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
