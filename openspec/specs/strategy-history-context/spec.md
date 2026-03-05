# Purpose

TBD

## Requirements

### Requirement: run_backtest passes prices_history in context

`run_backtest()` SHALL pass `prices_history` (a DataFrame slice of all prices up to and including the current rebalance date) as a keyword argument in the `**context` dict on every `get_target_weights()` call during rebalance events.

#### Scenario: prices_history available at rebalance
- **WHEN** a rebalance occurs on date D
- **THEN** `get_target_weights()` is called with `prices_history=prices_df.loc[:D]`

#### Scenario: prices_history not passed on initial allocation
- **WHEN** the very first allocation is made on the opening date (before any rebalance events)
- **THEN** `get_target_weights()` is called without `prices_history` in context (or with a single-row history)

#### Scenario: Existing strategies unaffected
- **WHEN** `FixRatio.get_target_weights()` or `VixRegimeAllocation.get_target_weights()` is called with `prices_history` in context
- **THEN** they ignore the extra kwarg and return the same weights as before

### Requirement: Strategies handle missing history gracefully

Any strategy that consumes `prices_history` SHALL implement a fallback (e.g., equal weights) when `prices_history` is `None` or has fewer rows than `lookback_days`.

#### Scenario: Insufficient history falls back to equal weights
- **WHEN** `prices_history` has fewer rows than the strategy's `lookback_days`
- **THEN** the strategy returns equal weights across its symbols rather than raising an error
