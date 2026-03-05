## Why

The library has one allocation strategy (`FixRatio`), but meaningful portfolio management requires dynamic, data-driven allocations. Adding Volatility Targeting, Dollar Neutral, and Beta Neutral completes the core strategy surface described in the dimension-2 doc, while the engine extension makes it easy to add any future strategies that need historical price context.

## What Changes

- **Engine extension**: `run_backtest()` passes `prices_history` (all prices up to and including `date`) in the `**context` dict on every `get_target_weights()` call — enables any strategy to compute rolling statistics without changing the protocol signature
- **`VolatilityTargeting`**: long-only strategy; weights ∝ 1/realized_vol per asset, normalized to sum to 1.0; configurable `lookback_days` and `target_vol` (optional cap)
- **`DollarNeutral`**: long-short strategy; user specifies long symbols and short symbols with fixed intra-book ratios; engine maintains net dollar exposure within a configurable `tolerance` band; weights can be negative
- **`BetaNeutral`**: long-short strategy; computes rolling OLS beta of each symbol vs a `benchmark_symbol`; solves for weights that make `sum(w_i × β_i) = 0`; weights can be negative
- **`__init__.py` exports**: all three new classes added to public API
- **Backtest engine**: relax the "weights must sum to 1.0" guard for strategies that explicitly declare `allows_short = True`

## Capabilities

### New Capabilities
- `volatility-targeting`: inverse-volatility weight allocation using rolling realized volatility
- `dollar-neutral`: long-short allocation keeping net dollar exposure near zero
- `beta-neutral`: long-short allocation targeting zero portfolio beta vs a benchmark
- `strategy-history-context`: engine passes `prices_history` slice in context on every rebalance call

### Modified Capabilities
- `backtest-engine`: `run_backtest()` now passes `prices_history` in context; weight-sum guard relaxed for long-short strategies

## Impact

- `src/tiportfolio/allocation.py`: three new strategy classes
- `src/tiportfolio/backtest.py`: `run_backtest()` passes `prices_history` in context; relaxed weight validation path
- `src/tiportfolio/__init__.py`: export new classes
- `tests/`: new test files for each strategy
- New dependency: `numpy` (already present); no new packages required
