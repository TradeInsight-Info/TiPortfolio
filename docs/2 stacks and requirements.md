
> This project is built and tested with Python 3.12, however, it should be compatible with Python 3.10 and above.


## Basic Stacks
- Python 3.12
- Pandas
- NumPy
- Alpacy.Py or YFinance from src/tiportgolio/helpers for data source




- Target to simple to use and can be used out of box without too much configuration
  - easy to use like PyBroker
  - powerful on asset allocation like [Riskfolio-Lib](https://riskfolio-lib.readthedocs.io/en/latest/index.html) A library for making quantitative strategic asset allocation.



- Every steps of decision to rebalance will be recorded, and can be displayed in an interactive Plotly  chart or table.
  - It will also generate trading signals when rebalancing, to include the buy, sell and quantity to trade of each asset. Which is similar to the output of decisions dataframe from the engine running result. This will bring this library to be easily used in trading system. It receives a range of history data and return a latest signal, for example, feeding 252 days of data and return a signal of today's rebalance decision.
- Each step the performance methics will be calculated and displayed, like Sharpe Ratio, Max Drawdown, CAGR, Mar Ratio, End Portfolio Value etc.
- At end of backtest, a summary report will be generated, including the performance metrics, the allocation, the rebalance decisions, and the portfolio snapshot. This report will generate an interactive chart to show the portfolio value and each step when rebalance happened.
- Comparing function, give same results, can compare different allocation strategies, and different rebalance strategies and give summary report and an interactive chart to show the portfolio value.
- Use test/data as a sample data source for quick local testing and debugging.



