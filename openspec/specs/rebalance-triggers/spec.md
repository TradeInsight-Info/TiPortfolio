# Purpose

TBD

## Requirements

### Requirement: Scheduled rebalance every Monday

The system SHALL support scheduled rebalance every Monday, with dates aligned to nearest NYSE trading days.

#### Scenario: Monday rebalance dates generated
- **WHEN** schedule is set to "weekly_monday" and trading dates span multiple Mondays
- **THEN** rebalance dates include each Monday adjusted to the closest trading day

### Requirement: Scheduled rebalance every Wednesday

The system SHALL support scheduled rebalance every Wednesday, with dates aligned to nearest NYSE trading days.

#### Scenario: Wednesday rebalance dates generated
- **WHEN** schedule is set to "weekly_wednesday" and trading dates span multiple Wednesdays
- **THEN** rebalance dates include each Wednesday adjusted to the closest trading day

### Requirement: Scheduled rebalance every Friday

The system SHALL support scheduled rebalance every Friday, with dates aligned to nearest NYSE trading days.

#### Scenario: Friday rebalance dates generated
- **WHEN** schedule is set to "weekly_friday" and trading dates span multiple Fridays
- **THEN** rebalance dates include each Friday adjusted to the closest trading day

### Requirement: Scheduled rebalance never

The system SHALL support a "never" rebalance schedule that performs no rebalancing.

#### Scenario: No rebalance dates for never schedule
- **WHEN** schedule is set to "never"
- **THEN** empty DatetimeIndex is returned for rebalance dates

### Requirement: Volatility rebalance with freezing time

The system SHALL support volatility-based rebalance with a configurable freezing period in days to prevent rebalancing if the last rebalance occurred within that period.

#### Scenario: Rebalance skipped due to freezing
- **WHEN** VIX triggers rebalance but last rebalance was within freezing days
- **THEN** the rebalance is not performed

#### Scenario: Rebalance allowed after freezing period
- **WHEN** VIX triggers rebalance and last rebalance was more than freezing days ago
- **THEN** the rebalance is performed

---

### Requirement: VIX Regime Signal Delay

`_vix_regime_rebalance_dates()` SHALL accept a `signal_delay: int` parameter. When a VIX threshold crossing is detected on day T, the resulting rebalance date SHALL be the trading day at index `idx(T) + signal_delay` in the `trading_dates` array.

#### Scenario: VIX crosses upper threshold with delay=1
- **WHEN** VIX is below `upper_thresh` on day T-1 and at or above `upper_thresh` on day T
- **AND** `signal_delay=1`
- **THEN** the rebalance date SHALL be T+1 (the next trading day after T)

#### Scenario: VIX crosses lower threshold with delay=1
- **WHEN** VIX is above `lower_thresh` on day T-1 and at or below `lower_thresh` on day T
- **AND** `signal_delay=1`
- **THEN** the rebalance date SHALL be T+1 (the next trading day after T)

#### Scenario: Signal on last trading day is discarded
- **WHEN** VIX crosses a threshold on the last available trading day
- **AND** `signal_delay >= 1`
- **THEN** no rebalance date SHALL be generated (the shifted date would fall outside the trading range)

#### Scenario: Duplicate date deduplication after shifting
- **WHEN** multiple VIX crossings on consecutive days T and T+1 both shift to the same execution day
- **THEN** only one rebalance date SHALL be generated for that day

---

### Requirement: get_rebalance_dates signal_delay Parameter

`get_rebalance_dates()` SHALL accept an optional `signal_delay: int` parameter (default `1`) and pass it to `_vix_regime_rebalance_dates()` when schedule is `vix_regime`.

#### Scenario: Calendar schedules ignore signal_delay
- **WHEN** `get_rebalance_dates()` is called with schedule `month_end` and `signal_delay=1`
- **THEN** the rebalance dates SHALL be identical to calling with `signal_delay=0`

---

### Requirement: VIX Change Filter Delay

When `VixChangeFilter` returns `True` on day T (indicating a rebalance should occur), the engine wrapper SHALL defer the actual rebalance to day T + `signal_delay` trading days.

#### Scenario: Filter fires on day T with delay=1
- **WHEN** `VixChangeFilter.__call__()` returns `True` for date T
- **AND** `signal_delay=1`
- **THEN** the engine SHALL schedule the rebalance for the next trading day after T
- **AND** `last_rebalance_date` SHALL be updated to the execution date (T+1), not the signal date

#### Scenario: Filter fires on day T with delay=0
- **WHEN** `VixChangeFilter.__call__()` returns `True` for date T
- **AND** `signal_delay=0`
- **THEN** the rebalance SHALL execute on day T (legacy behavior)
