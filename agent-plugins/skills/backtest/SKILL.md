---
name: backtest
description: >
  This skill should be used when the user wants to backtest, simulate, or evaluate
  a portfolio strategy, asset allocation, rebalancing plan, or dollar-cost averaging
  (DCA/AIP) using the tiportfolio CLI. Triggers on phrases like "backtest QQQ BIL GLD",
  "how would a 60/40 portfolio perform", "monthly DCA $1000 into SPY", "risk parity
  backtest", "buy and hold AAPL", "compare 1x vs 2x leverage",
  or when the user mentions tickers with allocation ratios and a time period.
---

# Backtest — Portfolio Strategy Simulator

Convert natural language backtesting requests into `tiportfolio` CLI commands, run them, and present results.

## Step 1: Ensure uvx is available

```bash
uvx --version > /dev/null 2>&1
```

- **If uvx exists** → proceed to Step 2. All commands use `uvx tiportfolio ...` (no install needed).
- **If uvx is not found** → tell the user:
  > `uvx` is required to run this skill. Install it from https://docs.astral.sh/uv/

Do NOT proceed until uvx is available.

## Step 2: Extract parameters from the user's request

Parse the user's message and map to CLI flags using this table:

| Parameter | CLI Flag | Default | Notes |
|-----------|----------|---------|-------|
| **Tickers** | `--tickers QQQ,BIL,GLD` | *(required)* | Ask the user if no tickers are mentioned |
| **Start date** | `--start <5y-ago>` | 5 years ago from today | Compute dynamically — never use hardcoded dates |
| **End date** | `--end <today>` | Today's date | Compute dynamically — never use hardcoded dates |
| **Frequency** | subcommand: `monthly`, `quarterly`, `weekly`, `yearly`, `once` | `monthly` | "rebalance monthly" → `monthly` |
| **Equal weight** | `--ratio equal` | `equal` | Default when no ratio specified |
| **Custom ratio** | `--ratio 0.6,0.4` | — | "60/40" → `0.6,0.4`; "70/20/10" → `0.7,0.2,0.1` |
| **ERC / risk parity** | `--ratio erc` | — | "risk parity" or "ERC" |
| **Volatility target** | `--ratio hv --target-hv 0.10` | — | "target 10% vol" |
| **AIP / DCA** | `--aip 1000` | — | "$1000 monthly" or "DCA $1000" |
| **Leverage** | `--leverage 1.5` | — | "1.5x leverage" |
| **Compare leverage** | `--leverage 1.0,1.5,2.0` | — | "compare 1x, 1.5x, 2x" |
| **Full summary** | `--full` | off | "detailed" or "full summary" |
| **Save chart** | `--plot chart.png` | — | "save chart" or "show chart" |
| **Momentum selection** | `--select momentum --top-n N` | — | "top 3 by momentum" |
| **Lookback** | `--lookback 90d` | — | "90 day lookback" — only applies with `--select momentum` |
| **CSV data** | `--csv /path/to/dir` | — | "use local CSV data" or "offline mode" |

### Ratio conversion rules

- Percentages: "60/40" → `0.6,0.4` — "70/20/10" → `0.7,0.2,0.1`
- Named: "equal weight" → `equal` — "risk parity" → `erc`
- If ratios don't sum to 1.0, normalize them

## Step 3: Build and show the command

Construct the full CLI command. **Always show it to the user before running**, so they can verify:

> Running: `uvx tiportfolio monthly --tickers QQQ,BIL,GLD --start <5y-ago> --end <today> --ratio equal`


## Step 4: Run the command

Execute via the Bash tool:

```bash
uvx tiportfolio <subcommand> --tickers <tickers> --start <start> --end <end> --ratio <ratio> [--aip <amount>] [--leverage <lev>] [--full] [--plot <path>]
```

## Step 5: Present results

- Show the summary table from stdout
- Highlight key metrics: **Sharpe**, **CAGR**, **max drawdown**, **final value**
- If AIP was used, also highlight **total contributions** and **contribution count**
- Offer follow-ups:
  - "Want the full summary?" → re-run with `--full`
  - "Save a chart?" → re-run with `--plot backtest.png` then show the image

## Step 6: Handle errors

If the command fails:
- Show the error message
- Suggest common fixes:
  - "Invalid ticker" → check spelling, use standard ticker symbols
  - "No data" → try a different date range or data source
  - "Ratio count mismatch" → number of ratios must match number of tickers

## Examples

### Basic equal-weight backtest
**User**: "Backtest QQQ BIL GLD equal weight monthly from 2019 to 2024"
**Command**: `uvx tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal`

### Custom ratio
**User**: "70/20/10 allocation of QQQ BIL GLD quarterly"
**Command**: `uvx tiportfolio quarterly --tickers QQQ,BIL,GLD --start <5y-ago> --end <today> --ratio 0.7,0.2,0.1`

### Dollar-cost averaging
**User**: "Monthly $1000 DCA into QQQ BIL GLD equal weight"
**Command**: `uvx tiportfolio monthly --tickers QQQ,BIL,GLD --start <5y-ago> --end <today> --ratio equal --aip 1000`

### Leverage comparison
**User**: "Compare 1x vs 1.5x vs 2x leverage on monthly QQQ BIL GLD"
**Command**: `uvx tiportfolio monthly --tickers QQQ,BIL,GLD --start <5y-ago> --end <today> --ratio equal --leverage 1.0,1.5,2.0`

### Buy and hold
**User**: "Buy and hold AAPL from 2020 to 2024"
**Command**: `uvx tiportfolio once --tickers AAPL --start 2020-01-01 --end 2024-12-31 --ratio equal`

### Risk parity with full summary
**User**: "Risk parity QQQ BIL GLD monthly, show me the full details"
**Command**: `uvx tiportfolio monthly --tickers QQQ,BIL,GLD --start <5y-ago> --end <today> --ratio erc --full`

### Momentum top-N selection
**User**: "Top 3 by momentum from QQQ BIL GLD AAPL, 90 day lookback, monthly"
**Command**: `uvx tiportfolio monthly --tickers QQQ,BIL,GLD,AAPL --start <5y-ago> --end <today> --ratio equal --select momentum --top-n 3 --lookback 90d`

### Offline with local CSV data
**User**: "Backtest QQQ BIL GLD using local CSV files in ./data"
**Command**: `uvx tiportfolio monthly --tickers QQQ,BIL,GLD --start <5y-ago> --end <today> --ratio equal --csv ./data`

### Minimal request (use all defaults)
**User**: "Backtest QQQ and BIL"
**Command**: `uvx tiportfolio monthly --tickers QQQ,BIL --start <5y-ago> --end <today> --ratio equal`
