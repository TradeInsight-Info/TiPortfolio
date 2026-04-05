# TiPortfolio Documentation

A simple yet flexbile portfolio management tool with built-in state-of-the-art portfolio optimization algorithms, with extensibility for different use cases for both institutes and retail traders.

## Get started

> Let's started with a simple monthly rebalance assest allocation strategy, it will equal weight the portfolio among QQQ, BIL and GLD at the end of each month. This is commonly used strategy to keep the portfolio balanced and diversified, to reduce risk.

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

# fetch data
data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31") # this will return a dict of dataframe, key is ticker, value is dataframe with date as index and columns like open, close, high, low, volume

# built strategy to rebalance monthly with fix ratio allocation among QQQ, BIL and GLD
portfolio = ti.Portfolio(
    'monthly_rebalance',
    [
        # Order matters
        ti.Signal.Monthly(), # When
        ti.Select.All(),       # What
        ti.Weigh.Equally(),    # How much
        ti.Action.Rebalance() # Action
    ],
    tickers # match tickers
)

test = ti.Backtest(portfolio, data)
result = ti.run(test)
```

### Checking the Backtest Result


#### Interactive Chart

```python
# plot result
result.plot()
```

![](assets/portfolio.png)


#### Key Metrics Summary
```python
# print key summary
result.summary()
```

```shell
                     value
sharpe               0.644
calmar               0.549
sortino              0.834
max_drawdown        -0.263
cagr                 0.144
risk_free_rate       0.040
total_return         1.564
kelly                3.787
final_value      25643.930
total_fee            0.941
rebalance_count     83.000
leverage             1.000
```

#### Trade Records
```python
# print trade records
result.trades
```

| date | portfolio | ticker | qty_before | qty_after | delta | price | fee | equity_before | equity_after |
|---|---|---|---|---|---|---|---|---|---|
| 2024-01-31 | monthly_rebalance | QQQ | 0.0 | 33.12 | 33.12 | 100.50 | 0.116 | 10000.0 | 9999.65 |


### Using TiPortfolio CLI:

> We can backtest a portfolio strategy through CLI without writing a single line of cod too:

```bash
# Install
pip install tiportfolio

# Run from CLI
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio 0.7,0.2,0.1
```
