## Why

Chunk 1 is implemented but has zero runnable examples. New users need copy-pasteable scripts to understand the API. Each example demonstrates one allocation pattern or feature using only Chunk 1 capabilities.

## What Changes

- **New** `examples/` directory with 5 standalone Python scripts
- Each script is a self-contained demo — fetch data, build portfolio, run backtest, print summary
- Scripts use real tickers via `ti.fetch_data` (yfinance) so users see real results

## Capabilities

### New Capabilities

- `example-scripts`: Standalone runnable Python files demonstrating Chunk 1 portfolio allocation patterns

### Modified Capabilities

_(none)_

## Impact

- **New files**: 5 Python scripts in `examples/`
- **No code changes**: Examples only use the existing public API
- **Dependencies**: None new — scripts use `tiportfolio` as installed
