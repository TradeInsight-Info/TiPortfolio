---
name: backtest
description: >
  Backtest, simulate, or evaluate a portfolio strategy, allocation, rebalancing
  plan, or DCA/AIP using the tiportfolio CLI. Triggers on "backtest QQQ BIL GLD",
  "60/40 portfolio", "monthly DCA $1000 into SPY", "risk parity backtest",
  "buy and hold AAPL", "compare 1x vs 2x leverage", or tickers named with
  allocation ratios and a time period.
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

Proceed only once uvx is available.

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
| **Data source** | `--source tidata` | `auto` | `auto` picks by configured keys: tidata → alpaca → yfinance. Force one to pin the source |

### Data source

- `auto` (default) selects a provider from whichever credentials are set:
  **tidata** (`TRADEINSIGHT_API_KEY`) → **alpaca** (`ALPACA_API_KEY`/`ALPACA_API_SECRET`) → **yfinance** (no key needed).
- Because `auto` depends on the environment, the same command can return
  different numbers on different machines. For a reproducible run, pass an
  explicit `--source` and report which one was used.

### Ratio normalization

- If custom ratios don't sum to 1.0, normalize them before passing to `--ratio`.

## Step 3: Build and show the command

Construct the full CLI command. Substitute real computed dates for `<5y-ago>`/`<today>` — never pass the placeholders literally. **Always show it to the user before running**, so they can verify:

> Running: `uvx tiportfolio monthly --tickers QQQ,BIL,GLD --start <5y-ago> --end <today> --ratio equal`


## Step 4: Run the command

Execute the exact command shown in Step 3 via the Bash tool.

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
  - "No data" → try a different date range, or force a provider with `--source yfinance`
  - "Ratio count mismatch" → number of ratios must match number of tickers

## Examples

Non-obvious combinations whose syntax isn't guessable from the table above. Basic cases (equal weight, custom ratio, buy-and-hold via `once`) map directly from the table.

### Dollar-cost averaging
**User**: "Monthly $1000 DCA into QQQ BIL GLD equal weight"
**Command**: `uvx tiportfolio monthly --tickers QQQ,BIL,GLD --start <5y-ago> --end <today> --aip 1000`

### Leverage comparison
**User**: "Compare 1x vs 1.5x vs 2x leverage on monthly QQQ BIL GLD"
**Command**: `uvx tiportfolio monthly --tickers QQQ,BIL,GLD --start <5y-ago> --end <today> --leverage 1.0,1.5,2.0`

### Momentum top-N selection
**User**: "Top 3 by momentum from QQQ BIL GLD AAPL, 90 day lookback, monthly"
**Command**: `uvx tiportfolio monthly --tickers QQQ,BIL,GLD,AAPL --start <5y-ago> --end <today> --select momentum --top-n 3 --lookback 90d`

### Offline with local CSV data
**User**: "Backtest QQQ BIL GLD using local CSV files in ./data"
**Command**: `uvx tiportfolio monthly --tickers QQQ,BIL,GLD --start <5y-ago> --end <today> --csv ./data`
