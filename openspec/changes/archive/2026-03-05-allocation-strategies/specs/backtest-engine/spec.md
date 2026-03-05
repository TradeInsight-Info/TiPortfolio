## MODIFIED Requirements

### Requirement: run_backtest passes prices_history in context on rebalance

`run_backtest()` SHALL pass `prices_history=prices_df.loc[:date]` as a keyword argument in the `**context` dict on every `get_target_weights()` call that occurs during a rebalance event.

This is a backward-compatible addition: existing strategies receive `prices_history` in `**context` and ignore it via `**context: Any`.

#### Scenario: prices_history slice passed on rebalance
- **WHEN** a rebalance occurs on date D
- **THEN** `get_target_weights()` is called with `prices_history=prices_df.loc[:D]` in context, containing all price rows from the start up to and including D

#### Scenario: prices_history is a DataFrame view not a copy
- **WHEN** `prices_df.loc[:D]` is passed
- **THEN** it is a pandas loc-slice (view or copy per pandas semantics), not an explicit `.copy()` call — O(n) memory is acceptable

#### Scenario: existing strategies unaffected
- **WHEN** `FixRatio.get_target_weights()` or `VixRegimeAllocation.get_target_weights()` is called with `prices_history` in context
- **THEN** they ignore the extra kwarg via `**context` and return the same weights as before

---

### Requirement: weight-sum validation relaxed for long-short strategies

`run_backtest()` SHALL NOT raise an error when `get_target_weights()` returns weights that include negative values, provided that the weights still sum to 1.0 ± 0.01.

The existing sum-to-1.0 guard REMAINS in place. Only the "all weights must be non-negative" implicit assumption is relaxed.

#### Scenario: negative weights accepted when sum is 1.0
- **WHEN** a strategy returns `{"SPY": 0.5, "QQQ": -0.5, "BIL": 1.0}` (sum = 1.0)
- **THEN** `run_backtest()` processes the rebalance without error

#### Scenario: weights summing away from 1.0 still rejected
- **WHEN** a strategy returns weights that sum to 0.6
- **THEN** a `ValueError` or warning is raised (existing behavior preserved)
