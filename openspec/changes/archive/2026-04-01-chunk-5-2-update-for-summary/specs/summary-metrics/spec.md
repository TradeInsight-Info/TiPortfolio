## MODIFIED Requirements

### Requirement: summary() metric ordering
The `summary()` method SHALL return metrics with the following top-5 order: `sharpe`, `calmar`, `sortino`, `max_drawdown`, `cagr`. Remaining metrics (`risk_free_rate`, `total_return`, `kelly`, `final_value`, `total_fee`, `rebalance_count`) SHALL follow in that order.

#### Scenario: Top 5 metrics appear first
- **WHEN** `summary()` is called on a `_SingleResult`
- **THEN** the DataFrame index positions 0–4 SHALL be `sharpe`, `calmar`, `sortino`, `max_drawdown`, `cagr` in that exact order

#### Scenario: All original metrics still present
- **WHEN** `summary()` is called
- **THEN** all 11 original metric keys SHALL still be present in the output

### Requirement: 3-decimal rounding
All float values in `summary()` and `full_summary()` output SHALL be rounded to 3 decimal places. Integer-like values (`rebalance_count`) SHALL remain as integers.

#### Scenario: summary() values are rounded
- **WHEN** `summary()` is called and a metric has value `0.12345`
- **THEN** it SHALL appear as `0.123` in the output DataFrame

#### Scenario: full_summary() values are rounded
- **WHEN** `full_summary()` is called
- **THEN** all float values SHALL have at most 3 decimal places

#### Scenario: rebalance_count remains integer
- **WHEN** `summary()` is called
- **THEN** `rebalance_count` SHALL remain an integer value, not rounded as a float
