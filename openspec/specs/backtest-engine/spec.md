# Purpose

TBD

## Requirements

### Requirement: Abstract BacktestEngine base class

The BacktestEngine SHALL be an abstract base class that cannot be instantiated directly, with shared initialization logic for subclasses.

#### Scenario: Direct instantiation raises error
- **WHEN** user attempts to instantiate BacktestEngine directly
- **THEN** TypeError is raised indicating it's an abstract class

#### Scenario: Subclasses inherit initialization
- **WHEN** a subclass of BacktestEngine is instantiated
- **THEN** the shared __init__ method sets allocation, rebalance, fee_per_share, initial_value, and risk_free_rate attributes correctly

### Requirement: BacktestResult summary output
`BacktestResult.summary()` SHALL return a human-readable string that includes `sharpe_ratio`, `sortino_ratio`, `mar_ratio`, `cagr`, `max_drawdown`, `kelly_leverage`, `mean_excess_return`, `final_value`, `total_fee`, and rebalance count, in that display order.

#### Scenario: Summary includes Sortino ratio
- **WHEN** `result.summary()` is called on a completed backtest
- **THEN** the returned string contains a line with "Sortino Ratio:" and a numeric value

#### Scenario: Summary includes mean excess return
- **WHEN** `result.summary()` is called on a completed backtest
- **THEN** the returned string contains a line with "Mean Excess Return:" and a numeric value

#### Scenario: Summary metric order
- **WHEN** `result.summary()` is called
- **THEN** Sharpe Ratio appears before Sortino Ratio, which appears before MAR Ratio, which appears before CAGR, which appears before Max Drawdown

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

---

### Requirement: compare_strategies top-5 metrics
`compare_strategies()` SHALL compare strategies on exactly 5 metrics: `sharpe_ratio`, `sortino_ratio`, `mar_ratio`, `cagr`, `max_drawdown`, in that order. `sortino_ratio` is higher-is-better.

#### Scenario: Comparison DataFrame has exactly 5 rows
- **WHEN** `compare_strategies()` is called with two or more BacktestResult instances
- **THEN** the returned DataFrame has exactly 5 rows with index `["sharpe_ratio", "sortino_ratio", "mar_ratio", "cagr", "max_drawdown"]`

#### Scenario: Sortino ratio comparison direction
- **WHEN** one strategy has a higher `sortino_ratio` than others
- **THEN** that strategy is identified as "better" in the `sortino_ratio` row

---

### Requirement: Signal Delay in Backtest Loop

`run_backtest()` SHALL accept an optional `signal_delay: int` parameter (default `1`) that controls the offset between signal observation and trade execution for signal-based rebalances.

#### Scenario: Default signal delay of 1
- **WHEN** `run_backtest()` is called without specifying `signal_delay`
- **THEN** the default value SHALL be `1`
- **AND** the behavior SHALL match `signal_delay=1`

#### Scenario: Legacy mode with signal_delay=0
- **WHEN** `run_backtest()` is called with `signal_delay=0`
- **THEN** the behavior SHALL match the pre-fix behavior (signal and execution on the same bar)

---

### Requirement: Signal-Day Prices History

On a rebalance day, the `prices_history` context passed to `allocation.get_target_weights()` SHALL be sliced to the **signal date**, not the execution date.

#### Scenario: prices_history excludes execution day data
- **WHEN** a rebalance occurs on trading day T+1 with `signal_delay=1`
- **THEN** `prices_history` SHALL be `prices_df.loc[:T]` where T is the signal date (one trading day before T+1)
- **AND** `prices_row` SHALL be `prices_df.loc[T+1]` (execution day close prices)

#### Scenario: signal_delay=0 preserves original behavior
- **WHEN** a rebalance occurs on trading day T with `signal_delay=0`
- **THEN** `prices_history` SHALL be `prices_df.loc[:T]`
- **AND** `prices_row` SHALL be `prices_df.loc[T]`

---

### Requirement: Signal Date in Context

The backtest loop SHALL pass `signal_date` in the context kwargs to `get_target_weights()` on rebalance days.

#### Scenario: signal_date available to allocation strategies
- **WHEN** `get_target_weights()` is called on rebalance day T+1 with `signal_delay=1`
- **THEN** `context['signal_date']` SHALL equal T (one trading day before T+1)

---

### Requirement: Edge Case Early Trading Days

**WHEN** `signal_delay > 0` and the rebalance date minus delay falls before the first trading date, **THEN** the signal date SHALL be clamped to the first trading date **AND** `prices_history` SHALL include at minimum the first trading day.

---

### Requirement: Engine signal_delay Threading

`BacktestEngine.__init__()` SHALL accept an optional `signal_delay: int` parameter (default `1`) and store it as an instance attribute. It SHALL be passed through to `run_backtest()`. Values less than `0` SHALL raise `ValueError`.

#### Scenario: ScheduleBasedEngine passes signal_delay
- **WHEN** `ScheduleBasedEngine(signal_delay=2)` is constructed and `run()` is called
- **THEN** `run_backtest()` SHALL receive `signal_delay=2`

#### Scenario: VolatilityBasedEngine passes signal_delay
- **WHEN** `VolatilityBasedEngine(signal_delay=1)` is constructed and `run()` is called
- **THEN** both `get_rebalance_dates()` and `run_backtest()` SHALL receive `signal_delay=1`

#### Scenario: Negative signal_delay raises ValueError at construction
- **WHEN** any BacktestEngine subclass is constructed with `signal_delay=-1`
- **THEN** `ValueError` is raised with a message including the invalid value
