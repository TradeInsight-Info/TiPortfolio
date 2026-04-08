# TiPortfolio

A portfolio management tool with built-in state-of-the-art portfolio optimization algorithms, with extensibility for different use cases for both institutes and retail traders.

**[Documentation](https://tiportfolio.tradeinsight.info/)** | **[PyPI](https://pypi.org/project/tiportfolio/)** | **[GitHub](https://github.com/TradeInsight-Info/TiPortfolio)**


## Quick Start


```bash
pip install tiportfolio

# For interactive Plotly charts:
pip install tiportfolio[interactive]

# For Equal Risk Contribution (ERC) weighting:
pip install tiportfolio[erc]
```

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

## CLI

Run backtests directly from the terminal — no Python script needed.


Use `pipx install tiportfolio --python python3.12` to install the CLI tool globally without affecting your Python environment. 

Or use uvx to run the CLI without installing: `uvx run tiportfolio -- [options]` instead of `tiportfolio [options]`.


```bash
# Monthly rebalance QQQ/BIL/GLD at 70/20/10
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio 0.7,0.2,0.1

# Quarterly equal-weight rebalance
tiportfolio quarterly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal

# Compare at 1x, 1.5x, 2x leverage (includes borrowing cost)
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio 0.7,0.2,0.1 --leverage 1.0,1.5,2.0

# Save equity curve chart
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal --plot chart.png
```

See [docs/cli.md](docs/cli.md) for the full CLI reference with all subcommands and options.

## Agent Skill

TiPortfolio includes an agent skill that lets you backtest strategies using natural language — no CLI flags to remember.

**Install the skill** for any agent that supports the [Skills](https://github.com/vercel-labs/skills) standard:

```bash
npx skills add https://github.com/TradeInsight-Info/TiPortfolio
```

For [Claude Code](https://docs.anthropic.com/en/docs/claude-code) specifically:

```bash
claude plugin add https://github.com/TradeInsight-Info/TiPortfolio
```

**Then just ask your agent:**

> "Backtest QQQ BIL GLD equal weight monthly from 2019 to 2024"

> "Monthly $1000 DCA into QQQ BIL GLD"

> "Compare 1x vs 1.5x vs 2x leverage on quarterly QQQ BIL GLD"

The skill maps your request to `uvx tiportfolio` CLI commands, runs the backtest, and presents the results. Requires [uv](https://docs.astral.sh/uv/) to be installed.

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
