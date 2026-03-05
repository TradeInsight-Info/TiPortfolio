# TiPortfolio

TiPortfolio is a portfolio management tool with built-in state-of-the-art portfolio optimization algorithms, with extensibility for different use cases for both institutes and retail traders.

This project is inspired by these two projects:

- [PyBroker](https://www.pybroker.com/en/latest/index.html) / [TiBacktester](https://pypi.org/project/tibacktester/) An easy to use backtest library.
- [Riskfolio-Lib](https://riskfolio-lib.readthedocs.io/en/latest/index.html) A library for making quantitative strategic asset allocation.

TiPortfolio is trying to be a portfolio optimisation library, it can backtest as easy as PyBroker,
and it can be extended to different algorithms similar to Riskfolio-Lib. In another word, it is a more practical version of Riskfolio-Lib with backtesting support.

- Simple and Easy To Use
- Library first, but with CLI support
- Flexible and Extensible, it can be configured easily to backtest different combination between different [rebalancing triggers](./dimensions/dimension 1 trigger of rebalance.md) and  different [allocation strategies](./dimensions/dimension 2 allocation strategies.md), and extensible for users to customised and built their own rebalancing triggers and allocation strategies.
- Rebalance decisions table with interactive chart in the end report, whether to buy more, or sell more or hold the same amount with reason
- Support portfolio performance metrics in the end report




## Know more

Check [rebalance ideas](./rebalance_ideas/) and [why built this](./thoughts.md) for more details.



## Additional Notes

- [Other thoughts](./thoughts.md)
- [Books and papers about portfolio management](./papers.md)
- [Dimensions of Portfolio Management](./dimensions/)