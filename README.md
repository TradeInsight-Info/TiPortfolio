# TiPortfolio

A portfolio management tool with built-in state-of-the-art portfolio optimization algorithms, with extensibility for different use cases for both institutes and retail traders.

## Quick start (fetch by symbols)

Data is fetched automatically from Alpaca (if API keys are set) or Yahoo Finance:

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
        ti.algo.ScheduleMonthly(), # When
        ti.algo.Select(), # What
        ti.algo.Weigh(), # How much
        ti.algo.Rebalance() # Action
    ],
    tickers # match tickers
)

test = ti.Backtest(portfolio, data, fee_per_share=0.0035)
result = ti.run_backtest(test)
```


- More [examples](examples/README.md)


## Requirements

- Python 3.10+
- pandas, numpy
- matplotlib (optional, for report charts)

Data fetching uses Yahoo Finance by default. For Alpaca, set `ALPACA_API_KEY` and `ALPACA_API_SECRET` in your environment (see `.env.example`). If fetch fails for any reason, the library raises an error with message "Failed to fetch data: ...".

## Installation

```bash
uv sync
```

## License

Apache 2.0



