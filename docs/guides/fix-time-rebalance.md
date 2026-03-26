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
        ti.algo.ScheduleMonthly(),              # trigger: end of month
        ti.algo.SelectAll(),                    # select all tickers
        ti.algo.WeighFixedRatio(weights=target_ratio),  # fixed target weights
        ti.algo.Rebalance(),                    # execute trades
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
        ti.algo.ScheduleMonthly(day=15, next_trading_day=True),  # 15th or next trading day
        ti.algo.SelectAll(),
        ti.algo.WeighEqually(),
        ti.algo.Rebalance(),
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
        ti.algo.ScheduleQuarterly(months=[2, 5, 8, 11]),  # end of Feb/May/Aug/Nov
        ti.algo.SelectAll(),
        ti.algo.WeighEqually(),
        ti.algo.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))
```

> **Note:** Months `[2, 5, 8, 11]` are offset one month ahead of calendar quarter-ends (Mar/Jun/Sep/Dec) to avoid rebalancing on the same dates as most institutional investors, reducing market impact.

Or built manually with `Or` when you need per-month customisation:

```python
portfolio = ti.Portfolio(
    'quarterly_rebalance',
    [
        ti.branching.Or(
            ti.algo.Schedule(month=2),
            ti.algo.Schedule(month=5),
            ti.algo.Schedule(month=8),
            ti.algo.Schedule(month=11),
        ),
        ti.algo.SelectAll(),
        ti.algo.WeighEqually(),
        ti.algo.Rebalance(),
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
        ti.branching.Or(
            ti.algo.Schedule(day=15, next_trading_day=True, month=2),
            ti.algo.Schedule(day=15, next_trading_day=True, month=8),
        ),
        ti.algo.SelectAll(),
        ti.algo.WeighEqually(),
        ti.algo.Rebalance(),
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
        ti.algo.Schedule(day=15, next_trading_day=True, month=7),
        ti.algo.SelectAll(),
        ti.algo.WeighEqually(),
        ti.algo.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))
```
