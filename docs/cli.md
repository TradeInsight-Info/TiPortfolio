# CLI Reference

TiPortfolio provides a `tiportfolio` command-line tool for running backtests without writing Python.

## Installation

```bash
pip install tiportfolio
```

The `tiportfolio` command is automatically available after installation.

## Quick Examples

```bash
# Monthly rebalance QQQ/BIL/GLD at 70/20/10
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio 0.7,0.2,0.1

# Quarterly equal-weight
tiportfolio quarterly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal

# Compare at 1x, 1.5x, 2x leverage
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio 0.7,0.2,0.1 --leverage 1.0,1.5,2.0
```

## Subcommands

Each subcommand maps to a rebalance frequency.

### monthly

Rebalance on a configured day each month.

```bash
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal --day start
```

Options: `--day` (start, mid, end — default: end)

### quarterly

Rebalance quarterly on configured months.

```bash
tiportfolio quarterly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal
tiportfolio quarterly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal --months 3,6,9,12
```

Options: `--day` (default: end), `--months` (default: 1,4,7,10)

### weekly

Rebalance weekly.

```bash
tiportfolio weekly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal
```

Options: `--day` (default: end)

### yearly

Rebalance yearly.

```bash
tiportfolio yearly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal
tiportfolio yearly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal --month 6
```

Options: `--day` (default: end), `--month` (1-12)

### every

Rebalance every N periods.

```bash
tiportfolio every --n 5 --period day --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal
tiportfolio every --n 2 --period month --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal
```

Options: `--n` (required), `--period` (required: day, week, month, year), `--day` (default: end)

### once

Buy-and-hold — rebalance once at the start.

```bash
tiportfolio once --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio 0.7,0.2,0.1
```

## Weighting (--ratio)

| Value | Strategy | Example |
|---|---|---|
| `equal` | Equal weight | `--ratio equal` |
| `0.7,0.2,0.1` | Explicit weights | `--ratio 0.7,0.2,0.1` |
| `erc` | Equal Risk Contribution | `--ratio erc --lookback 90d` |
| `hv` | Volatility targeting | `--ratio hv --target-hv 0.10 --lookback 90d` |

```bash
# ERC risk parity
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio erc --lookback 90d

# Volatility targeting at 10%
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio hv --target-hv 0.10 --lookback 60d
```

## Selection (--select)

| Value | Strategy | Extra options |
|---|---|---|
| `all` | All tickers (default) | — |
| `momentum` | Top-N by momentum | `--top-n`, `--lookback` |

```bash
# Monthly, pick top-2 by 90-day momentum, equal weight
tiportfolio monthly --tickers QQQ,BIL,GLD,AAPL --start 2019-01-01 --end 2024-12-31 --select momentum --top-n 2 --lookback 90d --ratio equal
```

## Leverage (--leverage)

Apply post-simulation leverage with borrowing cost deduction.

```bash
# Single leverage
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal --leverage 1.5

# Compare multiple leverage levels side-by-side
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio 0.7,0.2,0.1 --leverage 1.0,1.5,2.0
```

When a comma-separated list is provided, multiple identical backtests are created and compared at each leverage level.

## Output Options

```bash
# Full extended summary
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal --full

# Save equity curve chart
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal --plot chart.png
```

## Config Overrides

```bash
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal \
    --capital 50000 --fee 0.01 --rf 0.05
```

| Flag | Description | Default |
|---|---|---|
| `--capital` | Initial capital | 10000 |
| `--fee` | Fee per share | 0.0035 |
| `--rf` | Risk-free rate | 0.04 |

## Offline Mode (--csv)

Use local CSV files instead of fetching from Yahoo Finance:

```bash
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal --csv tests/data/
```

The `--csv` directory is scanned for files matching ticker names (e.g., `qqq_2018_2024_yf.csv`).
