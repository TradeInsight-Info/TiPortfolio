# Spec Delta: backtest-engine

## MODIFIED: Signal Delay in Backtest Loop

### Requirement: signal-delay-parameter

`run_backtest()` SHALL accept an optional `signal_delay: int` parameter (default `1`) that controls the offset between signal observation and trade execution for signal-based rebalances.

#### Scenario: Default signal delay of 1

WHEN `run_backtest()` is called without specifying `signal_delay`
THEN the default value SHALL be `1`
AND the behavior SHALL match `signal_delay=1`

#### Scenario: Legacy mode with signal_delay=0

WHEN `run_backtest()` is called with `signal_delay=0`
THEN the behavior SHALL match the pre-fix behavior (signal and execution on the same bar)

### Requirement: signal-day-prices-history

On a rebalance day, the `prices_history` context passed to `allocation.get_target_weights()` SHALL be sliced to the **signal date**, not the execution date.

#### Scenario: prices_history excludes execution day data

WHEN a rebalance occurs on trading day T+1 with `signal_delay=1`
THEN `prices_history` SHALL be `prices_df.loc[:T]` where T is the signal date (one trading day before T+1)
AND `prices_row` SHALL be `prices_df.loc[T+1]` (execution day close prices)

#### Scenario: signal_delay=0 preserves original behavior

WHEN a rebalance occurs on trading day T with `signal_delay=0`
THEN `prices_history` SHALL be `prices_df.loc[:T]`
AND `prices_row` SHALL be `prices_df.loc[T]`

### Requirement: signal-date-in-context

The backtest loop SHALL pass `signal_date` in the context kwargs to `get_target_weights()` on rebalance days.

#### Scenario: signal_date available to allocation strategies

WHEN `get_target_weights()` is called on rebalance day T+1 with `signal_delay=1`
THEN `context['signal_date']` SHALL equal T (one trading day before T+1)

### Requirement: edge-case-early-trading-days

WHEN `signal_delay > 0` and the rebalance date minus delay falls before the first trading date
THEN the signal date SHALL be clamped to the first trading date
AND `prices_history` SHALL include at minimum the first trading day

## MODIFIED: Engine signal_delay Threading

### Requirement: engine-signal-delay-parameter

`BacktestEngine.__init__()` SHALL accept an optional `signal_delay: int` parameter (default `1`) and store it as an instance attribute. It SHALL be passed through to `run_backtest()`.

#### Scenario: ScheduleBasedEngine passes signal_delay

WHEN `ScheduleBasedEngine(signal_delay=2)` is constructed and `run()` is called
THEN `run_backtest()` SHALL receive `signal_delay=2`

#### Scenario: VolatilityBasedEngine passes signal_delay

WHEN `VolatilityBasedEngine(signal_delay=1)` is constructed and `run()` is called
THEN both `get_rebalance_dates()` and `run_backtest()` SHALL receive `signal_delay=1`
