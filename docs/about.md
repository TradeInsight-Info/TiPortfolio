# TiPortfolio

TiPortfolio is a portfolio management tool with built-in state-of-the-art portfolio optimization algorithms, with extensibility for different use cases for both institutes and retail traders.

- Simple and Easy To Use
- Library first, but with CLI support
- Flexible and Extensible, it can be configured easily to backtest different combination between different [rebalancing triggers](./dimensions/dimension 1 trigger of rebalance.md) and  different [allocation strategies](./dimensions/dimension 2 allocation strategies.md), and extensible for users to customised and built their own rebalancing triggers and allocation strategies.
- Rebalance decisions table with interactive chart in the end report, whether to buy more, or sell more or hold the same amount with reason
- Support portfolio performance metrics in the end report


## Structure

`src/tiportfolio

- `__init__.py`
- `helpers/` to handle data fetching, processing, and other helper functions
- `algo.py` to handle different algorithms for rebalancing trigger and allocation strategy, and also the algo stack and tree structure
- `portfolio.py` to handle the portfolio structure
- `backtest.py` to handle the backtesting process, and also the result report generation


## Know more

This project is inspired by these projects:

- [PyBroker](https://www.pybroker.com/en/latest/index.html) / [TiBacktester](https://pypi.org/project/tibacktester/) An easy to use backtest library.
- [Riskfolio-Lib](https://riskfolio-lib.readthedocs.io/en/latest/index.html) A library for making quantitative strategic asset allocation.
- [bt](https://pmorissette.github.io/bt/) A flexible backtesting framework for Python used to test and develop trading strategies.