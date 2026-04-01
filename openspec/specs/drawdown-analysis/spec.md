## ADDED Requirements

### Requirement: Drawdown analysis metrics in full_summary()
The `full_summary()` method SHALL include drawdown analysis metrics: `avg_drawdown`, `avg_drawdown_days`, `avg_up_month`, `avg_down_month`, `win_year_pct`, `win_12m_pct`.

#### Scenario: All drawdown analysis keys present
- **WHEN** `full_summary()` is called
- **THEN** the output SHALL contain all 6 drawdown analysis keys

### Requirement: avg_drawdown computation
`avg_drawdown` SHALL be the mean trough depth of all drawdown episodes. A drawdown episode starts when equity drops below its cumulative max and ends when equity recovers to a new high. The depth is the minimum `(equity - cummax) / cummax` within each episode.

#### Scenario: avg_drawdown for monotonically increasing equity
- **WHEN** `full_summary()` is called on an equity curve that never drops
- **THEN** `avg_drawdown` SHALL be `0.0`

#### Scenario: avg_drawdown for equity with drawdowns
- **WHEN** `full_summary()` is called on an equity curve with drawdown episodes
- **THEN** `avg_drawdown` SHALL be a negative float representing the mean trough depth

### Requirement: avg_drawdown_days computation
`avg_drawdown_days` SHALL be the mean number of calendar days across all drawdown episodes (from first day below peak to recovery day or end of series).

#### Scenario: No drawdowns
- **WHEN** equity never drops below its cumulative max
- **THEN** `avg_drawdown_days` SHALL be `0`

### Requirement: avg_up_month and avg_down_month
`avg_up_month` SHALL be the mean of all positive monthly returns. `avg_down_month` SHALL be the mean of all negative monthly returns.

#### Scenario: Mixed monthly returns
- **WHEN** `full_summary()` is called on equity with both positive and negative months
- **THEN** `avg_up_month` SHALL be positive and `avg_down_month` SHALL be negative

#### Scenario: All positive months
- **WHEN** all monthly returns are positive
- **THEN** `avg_down_month` SHALL be `0.0`

### Requirement: win_year_pct
`win_year_pct` SHALL be the percentage of calendar years with a positive annual return.

#### Scenario: Win year percentage
- **WHEN** `full_summary()` is called on multi-year equity
- **THEN** `win_year_pct` SHALL be between `0.0` and `1.0`

### Requirement: win_12m_pct
`win_12m_pct` SHALL be the percentage of rolling 12-month windows that have a positive return.

#### Scenario: Rolling 12-month windows
- **WHEN** `full_summary()` is called on equity spanning at least 13 months
- **THEN** `win_12m_pct` SHALL be between `0.0` and `1.0`

#### Scenario: Insufficient data for rolling windows
- **WHEN** equity spans fewer than 13 months
- **THEN** `win_12m_pct` SHALL be `0.0`
