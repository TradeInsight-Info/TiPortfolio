## Why

Two cleanups from Chunk 1 feedback:
1. `fee_per_share` as a Backtest parameter is redundant — TiConfig already holds it. Having two places to set the same value is confusing.
2. Buy-and-hold (no rebalance) is a fundamental strategy that should be expressible, but the current design has no signal that fires only once.

## What Changes

- **Remove** `fee_per_share` parameter from `Backtest.__init__` — **BREAKING** for anyone using `Backtest(portfolio, data, fee_per_share=0.01)`; migration: use `TiConfig(fee_per_share=0.01)` instead
- **New** `Signal.Once()` — fires True on the first call, False on all subsequent calls
- **New** `examples/06_buy_and_hold.py` — demonstrates buy-and-hold QQQ/BIL/GLD

## Capabilities

### New Capabilities

- `signal-once`: Signal.Once algo that fires exactly once (enables buy-and-hold strategies)

### Modified Capabilities

- `backtest-api`: Remove fee_per_share convenience parameter from Backtest constructor

## Impact

- **Breaking**: `Backtest(fee_per_share=...)` no longer accepted — use `TiConfig(fee_per_share=...)` + `Backtest(config=...)`
- **Files modified**: backtest.py, test_backtest.py, signal.py, test_signal.py, 02_custom_config.py, api/index.md, spec
- **New file**: examples/06_buy_and_hold.py
