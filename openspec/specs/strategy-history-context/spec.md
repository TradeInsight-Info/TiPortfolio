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

---

### Requirement: Signal-Day Aligned History Window

When `signal_delay > 0`, `prices_history` passed in context to `get_target_weights()` SHALL be sliced to the signal date rather than the execution date.

#### Scenario: History window with signal_delay=1
- **WHEN** a rebalance executes on trading day T+1 with `signal_delay=1`
- **THEN** `prices_history` SHALL be `prices_df.loc[:T]`
- **AND** the last row of `prices_history` SHALL correspond to day T (the signal date)
- **AND** `prices_row` (execution prices) SHALL correspond to day T+1

#### Scenario: Strategies using prices_history for lookback
- **WHEN** `VolatilityTargeting` computes rolling volatility from `prices_history.tail(lookback_days + 1)`
- **AND** the rebalance executes on day T+1 with `signal_delay=1`
- **THEN** the lookback window SHALL end at day T (the signal date)
- **AND** day T+1's close price SHALL NOT appear in the lookback window

#### Scenario: BetaNeutral computes betas from signal-day history
- **WHEN** `BetaNeutral` computes rolling OLS betas from `prices_history`
- **AND** the rebalance executes on day T+1 with `signal_delay=1`
- **THEN** the beta estimation window SHALL end at day T
- **AND** day T+1's return SHALL NOT influence the beta estimate

---

### Requirement: signal_date Context Key

The context passed to `get_target_weights()` SHALL include a `signal_date` key on rebalance days when `signal_delay > 0`.

#### Scenario: DollarNeutral uses signal_date for tolerance check
- **WHEN** `DollarNeutral.get_target_weights()` is called with `signal_date` in context
- **THEN** the strategy MAY use `signal_date` to reconstruct signal-day position values for its tolerance check
- **AND** `positions_dollars` (argument) still reflects execution-day mark-to-market
