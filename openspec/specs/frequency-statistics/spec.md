## ADDED Requirements

### Requirement: Daily statistics in full_summary()
The `full_summary()` method SHALL include daily return statistics: `daily_mean_ann` (annualised), `daily_vol_ann` (annualised), `daily_skew`, `daily_kurt` (excess kurtosis), `best_day`, `worst_day`.

#### Scenario: All daily statistic keys present
- **WHEN** `full_summary()` is called
- **THEN** the output SHALL contain keys `daily_mean_ann`, `daily_vol_ann`, `daily_skew`, `daily_kurt`, `best_day`, `worst_day`

#### Scenario: daily_mean_ann is annualised correctly
- **WHEN** `full_summary()` is called with `bars_per_year=252`
- **THEN** `daily_mean_ann` SHALL equal `daily_returns.mean() * 252`

#### Scenario: daily_vol_ann is annualised correctly
- **WHEN** `full_summary()` is called with `bars_per_year=252`
- **THEN** `daily_vol_ann` SHALL equal `daily_returns.std() * sqrt(252)`

### Requirement: Monthly statistics in full_summary()
The `full_summary()` method SHALL include monthly return statistics: `monthly_sharpe`, `monthly_sortino`, `monthly_mean_ann`, `monthly_vol_ann`, `monthly_skew`, `monthly_kurt`, `best_month`, `worst_month`.

Monthly returns are derived from equity resampled to month-end frequency.

#### Scenario: All monthly statistic keys present
- **WHEN** `full_summary()` is called
- **THEN** the output SHALL contain all 8 monthly statistic keys

#### Scenario: monthly_mean_ann is annualised
- **WHEN** `full_summary()` is called
- **THEN** `monthly_mean_ann` SHALL equal `monthly_returns.mean() * 12`

#### Scenario: monthly_vol_ann is annualised
- **WHEN** `full_summary()` is called
- **THEN** `monthly_vol_ann` SHALL equal `monthly_returns.std() * sqrt(12)`

#### Scenario: monthly_sharpe uses risk-free rate
- **WHEN** `full_summary()` is called with `risk_free_rate=0.04`
- **THEN** `monthly_sharpe` SHALL equal `mean(monthly_excess) / std(monthly_excess) * sqrt(12)` where monthly excess = monthly_return - risk_free_rate/12

### Requirement: Yearly statistics in full_summary()
The `full_summary()` method SHALL include yearly return statistics: `yearly_sharpe`, `yearly_sortino`, `yearly_mean`, `yearly_vol`, `yearly_skew`, `yearly_kurt`, `best_year`, `worst_year`.

Yearly returns are derived from equity resampled to year-end frequency.

#### Scenario: All yearly statistic keys present
- **WHEN** `full_summary()` is called
- **THEN** the output SHALL contain all 8 yearly statistic keys

#### Scenario: yearly_mean is NOT annualised
- **WHEN** `full_summary()` is called
- **THEN** `yearly_mean` SHALL equal `yearly_returns.mean()` (already at annual frequency)

#### Scenario: Insufficient data for yearly stats
- **WHEN** `full_summary()` is called on an equity curve shorter than 2 years
- **THEN** yearly Sharpe and Sortino SHALL be `0.0` (not enough data points for meaningful std)
