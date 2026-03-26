## Comparing Results

`ti.run()` accepts multiple `Backtest` objects. When more than one is passed, all result methods automatically switch to comparison mode — metrics become a DataFrame and charts overlay all portfolios.


### Side-by-Side Comparison

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]
data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")

monthly = ti.Backtest(
    ti.Portfolio('monthly', [ti.algo.ScheduleMonthly(), ti.algo.SelectAll(), ti.algo.WeighEqually(), ti.algo.Rebalance()], tickers),
    data,
)
quarterly = ti.Backtest(
    ti.Portfolio('quarterly', [ti.algo.ScheduleQuarterly(), ti.algo.SelectAll(), ti.algo.WeighEqually(), ti.algo.Rebalance()], tickers),
    data,
)
yearly = ti.Backtest(
    ti.Portfolio('yearly', [ti.algo.Schedule(month=1), ti.algo.SelectAll(), ti.algo.WeighEqually(), ti.algo.Rebalance()], tickers),
    data,
)

result = ti.run(monthly, quarterly, yearly)
```


### Summary Table

```python
result.summary()
# Returns pd.DataFrame — rows are metrics, columns are portfolio names:
#
#                    monthly  quarterly  yearly
# total_return        0.42      0.39      0.35
# cagr                0.07      0.065     0.059
# daily_sharpe        0.91      0.88      0.84
# max_drawdown       -0.18     -0.19     -0.21
# ...
```

For the full metric set:

```python
result.full_summary()
# Same shape — pd.DataFrame with all daily/monthly/yearly stats per portfolio
```


### Overlaid Charts

```python
result.plot()                  # equity curves on one chart, one line per portfolio
result.plot_histogram()        # return distributions overlaid
result.plot_security_weights() # separate panel per portfolio
```


### Accessing Individual Results

Both positional index and portfolio name work regardless of how many tests were run:

```python
result[0]              # first portfolio's BacktestResult
result["monthly"]      # by portfolio name
result["quarterly"].summary()   # individual summary dict
result["quarterly"].trades      # individual trades DataFrame
```

This means you can always write `result[0]` even for a single backtest, making it easy to add comparisons later without changing the rest of your code.


### Comparing Allocation Strategies

A common pattern — test the same schedule with different weighting methods:

```python
import pandas as pd

tickers = ["QQQ", "BIL", "GLD"]
data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")

def monthly_portfolio(name, weigh_algo):
    return ti.Backtest(
        ti.Portfolio(name, [ti.algo.ScheduleMonthly(), ti.algo.SelectAll(), weigh_algo, ti.algo.Rebalance()], tickers),
        data,
    )

result = ti.run(
    monthly_portfolio("equal_weight",    ti.algo.WeighEqually()),
    monthly_portfolio("fixed_ratio",     ti.algo.WeighFixedRatio(weights={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1})),
    monthly_portfolio("vol_target",      ti.algo.WeighBasedOnHV(initial_ratio={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1}, target_hv=60, lookback=pd.DateOffset(months=1))),
    monthly_portfolio("erc",             ti.algo.WeighERC(lookback=pd.DateOffset(months=3))),
)

result.plot()
result.summary()
```
