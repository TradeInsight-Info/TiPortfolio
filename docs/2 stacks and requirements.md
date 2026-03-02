
## Basic Stacks
- Python 3.12
- Pandas
- NumPy
- Alpacy.Py or YFinance from src/tiportgolio/helpers for data source



TiPortfolio is a portfolio management tool with built-in state-of-the-art portfolio optimization algorithms, with extensibility for different use cases for both institutes and retail traders.


- Target to simple to use and can be used out of box without too much configuration
  - easy to use like PyBroker
  - powerful on asset allocation like [Riskfolio-Lib](https://riskfolio-lib.readthedocs.io/en/latest/index.html) A library for making quantitative strategic asset allocation.



- Every steps of decision to rebalance will be recorded, and can be displayed in a chart or table
- Each step the performance methics will be calculated and displayed, like Sharpe Ratio, Max Drawdown, CAGR, Mar Ratio etc.
- At end of backtest, a summary report will be generated, including the performance metrics, the allocation, the rebalance decisions, and the portfolio snapshot. This report will generate a chart to show the portfolio value and each step when rebalance happened.
- Comparing function, give same config (start end date, fee rate etc), can compare different allocation strategies, and different rebalance strategies and give summary report for each comparison.
- Use test/data as a sample data source for quick local testing and debugging.