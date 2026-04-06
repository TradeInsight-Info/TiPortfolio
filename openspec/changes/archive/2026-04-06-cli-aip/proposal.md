## Why

Users can now simulate AIP via `ti.run_aip()` in Python, but the CLI (`tiportfolio monthly ...`) only supports lump-sum backtesting. Many retail users prefer the CLI for quick experiments. Adding `--aip` lets them simulate dollar-cost averaging without writing code.

## What Changes

- Add `--aip <amount>` shared option to all CLI subcommands (monthly, quarterly, weekly, yearly, every, once)
- When `--aip` is provided, route to `ti.run_aip()` instead of `ti.run()`
- Summary output automatically includes `total_contributions` and `contribution_count` (already handled by `run_aip`)

**Current behavior**: AIP always injects on the last trading day of each month. Future enhancements will add `--aip-frequency` and `--aip-day` options, and corresponding `aip_frequency`/`aip_day` parameters to `run_aip()`.

**Example usage:**
```bash
# Monthly $1,000 AIP into equal-weight QQQ/BIL/GLD
tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio equal --aip 1000

# AIP works with any signal — the rebalance frequency is independent of AIP injection
tiportfolio quarterly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --aip 500
```

## Capabilities

### New Capabilities
- `cli-aip`: CLI `--aip` option for auto investment plan simulation across all subcommands

### Modified Capabilities
_None — existing CLI subcommands and run_aip() remain unchanged._

## Impact

- **Code**: `src/tiportfolio/cli.py` (~10 lines changed)
- **APIs**: New `--aip` CLI flag — additive, no breaking changes
- **Tests**: New `tests/test_cli_aip.py`
- **Dependencies**: None
