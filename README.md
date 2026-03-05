# TiPortfolio

A portfolio management tool with built-in state-of-the-art portfolio optimization algorithms, with extensibility for different use cases for both institutes and retail traders.
## Quick start (fetch by symbols)

Data is fetched automatically from Alpaca (if API keys are set) or Yahoo Finance:

```python
from tiportfolio import ScheduleBasedEngine, FixRatio, Schedule

engine = ScheduleBasedEngine(
    allocation=FixRatio(weights={"SPY": 0.5, "QQQ": 0.3, "GLD": 0.2}),
    rebalance=Schedule("month_end"),
    fee_per_share=0.0035,
)
result = engine.run(
    symbols=["SPY", "QQQ", "GLD"],
    start="2019-01-01",
    end="2024-12-31",
)

print(result.summary())
# result.equity_curve, result.metrics, result.rebalance_decisions
```


## Requirements

- Python 3.10+
- pandas, numpy
- matplotlib (optional, for report charts)

Data fetching uses Yahoo Finance by default. For Alpaca, set `ALPACA_API_KEY` and `ALPACA_API_SECRET` in your environment (see `.env.example`). If fetch fails for any reason, the library raises an error with message "Failed to fetch data: ...".

## Installation

```bash
uv sync
```

## CLI

**Symbols mode** (fetch data from Alpaca or Yahoo Finance; no CSV directory):

```bash
uv run tiportfolio --symbols SPY QQQ GLD --weights 0.5 0.3 0.2 --start 2019-01-01 --end 2024-12-31 --rebalance month_end
```


## License

Apache 2.0
