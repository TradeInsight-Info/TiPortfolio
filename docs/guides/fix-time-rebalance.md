


## Fix Time Rebalance Examples

These are example of how to rebalance a portfolio at a schedule time, it could be monthly, quarterly, yearly, or built your own schedule.



### Monthly Rebalance with Fixed Ratio Allocation
```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]
target_ratio = {
    "QQQ": 0.7,
    "BIL": 0.2,
    "GLD": 0.1
}

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31") 

portfolio = ti.Portfolio(
    'monthly_rebalance',
    [
        ti.algo.ScheduleMonthly(), # Monthly at the end of month
        ti.algo.Select(), # Select all tickers
        ti.algo.Weigh(target_ratio), # How much
        ti.algo.Rebalance() # Action
    ],
    tickers # match tickers
)


test = ti.Backtest(portfolio, data)
result = ti.run_backtest(test)
```


### Monthly (at Midlle of Month) Rebalance with Equal Weighting Allocation

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]


data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31") 

portfolio = ti.Portfolio(
    'monthly_rebalance_at_middle',
    [
        ti.algo.ScheduleMonthly(day=15, next_trading_day=True), # Rebalance at the middle of month, if the day is not trading day, then rebalance at the next closest trading day
        ti.algo.Select(), # What
        ti.algo.Weigh(), # Equal weight, if there is no target weight
        # or use ti.algo.WeighEqualy(), 
        ti.algo.Rebalance() # Action
    ],
    tickers # match tickers
)


test = ti.Backtest(portfolio, data)
result = ti.run_backtest(test)
```

### Quarterly Rebalance

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]


data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31") 

portfolio = ti.Portfolio(
    'quarterly_rebalance',
    [
        ti.branching.Or(
            [
                ti.algo.Schedule(month=2), # if no day is set, it will use end of month
                ti.algo.Schedule(month=5),
                ti.algo.Schedule(month=8),
                ti.algo.Schedule(month=11),
            ]
        ),
        ti.algo.Select(),
        ti.algo.Weigh(),
        ti.algo.Rebalance()
    ],
    tickers # match tickers
)

# or this can be simplfied to

portfolio = ti.Portfolio(
    'quarterly_rebalance',
    [
        ti.algo.Quarterly(dmonths=[2, 5, 8, 11]),,
        ti.algo.Select(),
        ti.algo.Weigh(),
        ti.algo.Rebalance()
    ],
    tickers # match tickers
)


test = ti.Backtest(portfolio, data)
result = ti.run_backtest(test)
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
            [
                ti.algo.Schedule(day=15, next_trading_day=True, month=2),
                ti.algo.Schedule(day=15, next_trading_day=True, month=8),
            ]
        ),
        ti.algo.Select(),
        ti.algo.Weigh(),
        ti.algo.Rebalance()
    ],
    tickers # match tickers
)


test = ti.Backtest(portfolio, data)
result = ti.run_backtest(test)
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
        ti.algo.Select(),
        ti.algo.Weigh(),
        ti.algo.Rebalance()
    ],
    tickers # match tickers
)


test = ti.Backtest(portfolio, data)
result = ti.run_backtest(test)
```