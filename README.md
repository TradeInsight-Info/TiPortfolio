# TiPortfolio

A portfolio management tool with built-in state-of-the-art portfolio optimization algorithms, with extensibility for different use cases for both institutes and retail traders.

## Installation

```bash
pip install tiportfolio

# For interactive Plotly charts:
pip install tiportfolio[interactive]

# For Equal Risk Contribution (ERC) weighting:
pip install tiportfolio[erc]
```

## Quick Start

```python
import tiportfolio as ti

# 1. Fetch data (Yahoo Finance by default, or Alpaca if API keys are set)
data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31")

# 2. Define strategy using the algo stack: Signal → Select → Weigh → Action
portfolio = ti.Portfolio(
    "monthly_equal_weight",
    [
        ti.Signal.Monthly(),    # WHEN to rebalance
        ti.Select.All(),        # WHAT to include
        ti.Weigh.Equally(),     # HOW MUCH to allocate
        ti.Action.Rebalance(),  # EXECUTE trades
    ],
    ["QQQ", "BIL", "GLD"],
)

# 3. Run backtest
result = ti.run(ti.Backtest(portfolio, data))

# 4. View results
result.summary()       # key metrics: Sharpe, CAGR, max drawdown, etc.
result.plot()          # equity curve + drawdown chart
```

- More [examples](examples/README.md)

## Requirements

- Python 3.10+
- pandas, numpy, matplotlib

Data fetching uses Yahoo Finance by default. For Alpaca, set `ALPACA_API_KEY` and `ALPACA_API_SECRET` in your environment (see `.env.example`).

## Development

```bash
uv sync
uv run python -m pytest
```

## License

Apache 2.0
