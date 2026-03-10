# Spec Delta: strategy-history-context

## MODIFIED: Signal-Day Aligned History Window

### Requirement: prices-history-aligned-to-signal-date

When `signal_delay > 0`, `prices_history` passed in context to `get_target_weights()` SHALL be sliced to the signal date rather than the execution date.

#### Scenario: History window with signal_delay=1

WHEN a rebalance executes on trading day T+1 with `signal_delay=1`
THEN `prices_history` SHALL be `prices_df.loc[:T]`
AND the last row of `prices_history` SHALL correspond to day T (the signal date)
AND `prices_row` (execution prices) SHALL correspond to day T+1

#### Scenario: Strategies using prices_history for lookback

WHEN `VolatilityTargeting` computes rolling volatility from `prices_history.tail(lookback_days + 1)`
AND the rebalance executes on day T+1 with `signal_delay=1`
THEN the lookback window SHALL end at day T (the signal date)
AND day T+1's close price SHALL NOT appear in the lookback window

#### Scenario: BetaNeutral computes betas from signal-day history

WHEN `BetaNeutral` computes rolling OLS betas from `prices_history`
AND the rebalance executes on day T+1 with `signal_delay=1`
THEN the beta estimation window SHALL end at day T
AND day T+1's return SHALL NOT influence the beta estimate

### Requirement: signal-date-context-key

The context passed to `get_target_weights()` SHALL include a `signal_date` key on rebalance days when `signal_delay > 0`.

#### Scenario: DollarNeutral uses signal_date for tolerance check

WHEN `DollarNeutral.get_target_weights()` is called with `signal_date` in context
THEN the strategy MAY use `signal_date` to reconstruct signal-day position values for its tolerance check
AND `positions_dollars` (argument) still reflects execution-day mark-to-market
