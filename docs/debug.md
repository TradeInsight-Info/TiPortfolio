## Debug in TiPortfolio


It is always hard to debug a trading strategy, especially when you backtest a long period of time, there are many trades, and it is hard to understand why a trade is made, and why the performance is like this.

TiPortfolio is designed to make it less painful to debug a trading strategy, we have the following features to help you debug your strategy:


### Interactive Chart

In the backtest result, we have an interactive chart, you can hover over the chart to see the performance at different time, and also you can click on the chart to see the trade records at that time, this will help you understand why a trade is made, and how it affects the performance.



### Use Sample


Use `sample` to get the more profitable trades and least profitable trades, this will help you understand whether the strategy is working as expected, and also you can analyze the trades to find out the potential improvement of the strategy.


``` python
# print sample trade records 10 top 10 profitable trades and -10 least profitable trades
result.trades.sample(10)
```



### Use Algo Info

Add this to your portfolio.

```python
portfolio = ti.Portfolio(
    'debug_example',
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.PrintInfo(),   # logs algo context at this point in the stack
        ti.Action.Rebalance(),
    ],
    tickers,
)
```



### Acurate metrics

- We have built in default value for risk free rate, benchmark ticker, fee rate etc, which will make the metrics more accurate, and also we can override these values through CLI arguments or config file, which will make it more flexible for users to use the library.