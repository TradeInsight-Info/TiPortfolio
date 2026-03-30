## Why

Chunk 1 delivered the foundation — a working backtest with monthly equal-weight rebalancing. But real portfolio strategies require branching logic (skip December rebalance, combine conditions), flexible scheduling (quarterly), data-driven selection (momentum), and non-equal weighting (fixed ratios, volatility targeting). Without these, users can only build the simplest toy strategies. Chunk 2 unlocks the full `fix-time-rebalance.md` examples and unblocks Chunks 3-4.

## What Changes

- **Branching combinators**: Add `Or`, `And`, `Not` as `Algo` subclasses — composable boolean logic for algo stacks
- **Signal expansion**: Add `Signal.Quarterly` (composes `Or` internally); complete `Signal.Schedule(day=int)` support (currently stubbed)
- **Selection expansion**: Add `Select.Momentum` (rank by lookback return) and `Select.Filter` (boolean gate using external data)
- **Weighting expansion**: Add `Weigh.Ratio` (explicit fixed weights) and `Weigh.BasedOnHV` (volatility-targeted scaling)
- **Public API**: Export `Or`, `And`, `Not` at `ti.*` level

No engine changes. No breaking changes to existing APIs.

## Capabilities

### New Capabilities

- `branching-combinators`: `Or`, `And`, `Not` algo composition — boolean logic for combining signals and conditions
- `quarterly-signal`: `Signal.Quarterly` and `Signal.Schedule(day=int)` — expanded time-based triggers
- `momentum-selection`: `Select.Momentum` — rank and select top-N tickers by lookback return
- `filter-selection`: `Select.Filter` — boolean gate using external data to halt/allow rebalance
- `ratio-weighting`: `Weigh.Ratio` — explicit fixed-weight allocation with normalisation
- `volatility-weighting`: `Weigh.BasedOnHV` — scale weights to target annualised portfolio volatility

### Modified Capabilities

_(none — all existing algos and engine behavior unchanged)_

## Impact

- **Code**: 3 modified source files (`algo.py`, `signal.py`, `select.py`, `weigh.py`), 1 modified init (`__init__.py`), 4 modified/new test files
- **APIs**: New public symbols `ti.Or`, `ti.And`, `ti.Not`; new algo classes under existing namespaces
- **Dependencies**: No new external dependencies (numpy already transitive via pandas)
- **Risk**: Low — pure additive changes to an existing plugin architecture
