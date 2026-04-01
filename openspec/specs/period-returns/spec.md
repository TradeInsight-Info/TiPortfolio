## ADDED Requirements

### Requirement: Period return calculations in full_summary()
The `full_summary()` method SHALL include trailing period returns computed from the equity curve. Each return measures `(end_value / start_value) - 1` over the specified lookback window from the last date. Multi-year periods (3y, 5y, 10y) SHALL be annualised using `(end/start)^(1/years) - 1`.

Keys: `mtd`, `3m`, `6m`, `ytd`, `1y`, `3y_ann`, `5y_ann`, `10y_ann`, `incep_ann`.

#### Scenario: All period return keys present
- **WHEN** `full_summary()` is called
- **THEN** the output SHALL contain all 9 period return keys: `mtd`, `3m`, `6m`, `ytd`, `1y`, `3y_ann`, `5y_ann`, `10y_ann`, `incep_ann`

#### Scenario: Period shorter than available data returns NaN
- **WHEN** `full_summary()` is called and the equity curve spans less than 3 years
- **THEN** `3y_ann`, `5y_ann`, `10y_ann` SHALL be `NaN` (not 0.0)

#### Scenario: MTD computes from start of current month
- **WHEN** `full_summary()` is called and the last equity date is 2023-12-29
- **THEN** `mtd` SHALL equal `(equity[-1] / equity[2023-12-01_or_nearest]) - 1`

#### Scenario: YTD computes from start of current year
- **WHEN** `full_summary()` is called and the last equity date is in 2023
- **THEN** `ytd` SHALL equal `(equity[-1] / equity[2023-01-01_or_nearest]) - 1`

#### Scenario: incep_ann is always computed
- **WHEN** `full_summary()` is called on any equity curve with more than 1 bar
- **THEN** `incep_ann` SHALL be the annualised return from first to last bar
