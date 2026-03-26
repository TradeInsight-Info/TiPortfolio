## Market Volatility Rebalance Example

In [fix-time-rebalance](./fix-time-rebalance.md) example, we have demonstrated how to use Strategy Stack to build a flexbile schedule trigger. 

In this part, we will show how to use Market Volatility (VIX) as a rebalance signal.

We have borrowed the [Tree Structure](https://pmorissette.github.io/bt/tree.html) concept from bt, which allows us to easily mix different portfolio strategies together, and use the VIX signal to switch between them to achieve a volatility based rebalance strategy.



```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31") 
vix_data = ti.fetch_data("VIX", start="2019-01-01", end="2024-12-31")


low_vol_portfolio = ti.Portfolio(
    'low_vol',
    [
        ti.algo.SelectAll(),
        ti.algo.Weigh({"QQQ":0.8, "BIL":0.15, "GLD":0.05}),
        ti.algo.Rebalance()
    ],
    tickers
)

high_vol_portfolio = ti.Portfolio(
    'high_vol',
    [
        ti.algo.SelectAll(),
        ti.algo.Weigh({"QQQ":0.5, "BIL":0.4, "GLD":0.1}),
        ti.algo.Rebalance()
    ],
    tickers
)

portfolio = ti.Portfolio(
    'vix_based_rebalance',
    [
        ti.algo.VixSignal(high=30, low=20, signal=vix_data), # we will preshift it, to avoid lookahead bias
        ti.algo.WeighSelected(1),
        ti.algo.Rebalance(),
    ],
    [low_vol_portfolio, high_vol_portfolio]
)

test = ti.Backtest(portfolio, data)
result = ti.run_backtest(test)
```
