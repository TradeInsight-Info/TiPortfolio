## Fix Time Rebalance Examples

These examples show how to rebalance a portfolio on a fixed schedule — monthly, quarterly, yearly, or a custom schedule built with `Or`.


### Monthly Rebalance with Fixed Ratio Allocation

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]
target_ratio = {"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1}

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")

portfolio = ti.Portfolio(
    'monthly_rebalance',
    [
        ti.Signal.Monthly(),              # trigger: end of month
        ti.Select.All(),                    # select all tickers
        ti.Weigh.Ratio(weights=target_ratio),  # fixed target weights
        ti.Action.Rebalance(),                    # execute trades
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))
```


### Monthly (Mid-Month) Rebalance with Equal Weighting

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")

portfolio = ti.Portfolio(
    'monthly_rebalance_mid',
    [
        ti.Signal.Monthly(day=15, next_trading_day=True),  # 15th or next trading day
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))
```


### Quarterly Rebalance

The built-in shortcut:

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")

portfolio = ti.Portfolio(
    'quarterly_rebalance',
    [
        ti.Signal.Quarterly(months=[2, 5, 8, 11]),  # end of Feb/May/Aug/Nov
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))
```

> **Note:** Months `[2, 5, 8, 11]` are offset one month ahead of calendar quarter-ends (Mar/Jun/Sep/Dec) to avoid rebalancing on the same dates as most institutional investors, reducing market impact.

Or built manually with `ti.Or` when you need per-month customisation:

```python
portfolio = ti.Portfolio(
    'quarterly_rebalance',
    [
        ti.Or(
            ti.Signal.Schedule(month=2),
            ti.Signal.Schedule(month=5),
            ti.Signal.Schedule(month=8),
            ti.Signal.Schedule(month=11),
        ),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    tickers,
)
```


### Every 6 Months Rebalance

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")

portfolio = ti.Portfolio(
    'half_year_rebalance',
    [
        ti.Or(
            ti.Signal.Schedule(day=15, next_trading_day=True, month=2),
            ti.Signal.Schedule(day=15, next_trading_day=True, month=8),
        ),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))
```


### Yearly Rebalance

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")

portfolio = ti.Portfolio(
    'yearly_rebalance',
    [
        ti.Signal.Schedule(day=15, next_trading_day=True, month=7),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))
```


## Branching: Or, And, Not

The algo stack runs top-to-bottom. Each algo can return `True` (continue) or `False` (stop). `Branch` operators let you compose conditions across multiple algos in a single stack position.

| Operator | Behaviour |
|---|---|
| `ti.Or(a, b)` | Passes if **any** inner algo passes |
| `ti.And(a, b)` | Passes only if **all** inner algos pass |
| `ti.Not(a)` | Passes if the inner algo does **not** pass |


### `ti.And` — require multiple conditions simultaneously

Rebalance only at month-end **and** only if the current month is not December (year-end tax harvest window):

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]
data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")

portfolio = ti.Portfolio(
    'monthly_skip_december',
    [
        ti.And(
            ti.Signal.Monthly(),
            ti.Not(ti.Signal.Schedule(month=12)),
        ),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))
```


### `ti.Not` — invert a signal

`ti.Not` wraps any single algo and flips its result. The example above shows the most common use: excluding a specific period from an otherwise-regular schedule.

Another example — select only the assets that the momentum filter would *not* select (i.e. the bottom performers):

```python
ti.Not(
    ti.Select.Momentum(n=3, lookback=pd.DateOffset(months=1), sort_descending=True)
)
```


### Combining all three

`Branch` operators nest freely. This triggers a rebalance when it is month-end **or** (it is mid-month **and** not in a freezing window):

```python
ti.Or(
    ti.Signal.Monthly(),
    ti.And(
        ti.Signal.Monthly(day=15, next_trading_day=True),
        ti.Not(ti.Signal.Schedule(month=12)),
    ),
)
```

> **Note:** Sequential algos in the stack are implicitly `And` — each one must pass for execution to continue. `ti.And` is only needed when you want to require two conditions *at the same stack position*.
