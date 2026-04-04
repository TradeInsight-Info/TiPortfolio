## Purpose

This capability adds an optional `leverage` parameter to the `run()` function, enabling users to simulate leveraged portfolio performance. Leverage scales daily returns by the specified factor and deducts a daily borrowing cost for the leveraged portion, accurately modeling financing costs while preserving compounding effects.

## Requirements

### Requirement: run() accepts leverage parameter
The `run()` function SHALL accept an optional keyword-only argument `leverage` of type `float | list[float]` with a default value of `1.0`.

#### Scenario: Default leverage (no argument)
- **WHEN** `run(bt)` is called without a `leverage` argument
- **THEN** the result SHALL be identical to the unleveraged backtest

#### Scenario: Single float leverage applied to all backtests
- **WHEN** `run(bt1, bt2, leverage=2.0)` is called with a single float
- **THEN** the leverage factor `2.0` SHALL be applied to every backtest result

#### Scenario: List of floats applied per-backtest
- **WHEN** `run(bt1, bt2, leverage=[1.5, 2.0])` is called with a list matching the number of backtests
- **THEN** leverage `1.5` SHALL be applied to `bt1` and `2.0` to `bt2`

#### Scenario: List length mismatch raises error
- **WHEN** `run(bt1, bt2, leverage=[1.5])` is called with a list whose length does not match the number of backtests
- **THEN** a `ValueError` SHALL be raised with a message indicating the mismatch

### Requirement: Leverage scales daily returns with borrowing cost
Leverage SHALL be applied by scaling each daily return of the equity curve by the leverage factor, then deducting the daily borrowing cost for the leveraged portion. The formula per day SHALL be: `leveraged_return = leverage × daily_return - (leverage - 1) × loan_rate / bars_per_year`. The `loan_rate` and `bars_per_year` SHALL come from the backtest's `TiConfig`. This preserves compounding effects and accurately models leveraged performance including financing costs.

#### Scenario: 2x leverage scales returns and deducts borrowing cost
- **WHEN** leverage=2.0 is applied to a backtest with loan_rate=0.0514, bars_per_year=252, and unleveraged day-1 return is +1%
- **THEN** the leveraged day-1 return SHALL be `2 × 1% - (2-1) × 0.0514/252` ≈ +1.9798%

#### Scenario: Borrowing cost applies even on down days
- **WHEN** leverage=2.0 is applied and the unleveraged day-1 return is -1%
- **THEN** the leveraged day-1 return SHALL be `2 × (-1%) - (2-1) × 0.0514/252` ≈ -2.0204%

#### Scenario: Leverage=1.0 is identity (no borrowing cost)
- **WHEN** leverage=1.0 is applied
- **THEN** the equity curve SHALL be unchanged because `(1-1) × loan_rate / bars_per_year = 0`

#### Scenario: Higher leverage incurs proportionally higher borrowing cost
- **WHEN** leverage=3.0 is applied with loan_rate=0.0514
- **THEN** the daily borrowing cost SHALL be `(3-1) × 0.0514/252` ≈ 0.0408% per day, reflecting borrowing 2x capital

### Requirement: Leverage metadata stored in result
The leverage factor SHALL be stored in `_SingleResult` and accessible in summary output.

#### Scenario: Summary includes leverage field
- **WHEN** `summary()` is called on a leveraged result
- **THEN** the summary DataFrame SHALL include a `leverage` row with the applied factor

#### Scenario: Unleveraged summary shows leverage=1.0
- **WHEN** `summary()` is called on a result with default leverage
- **THEN** the `leverage` row SHALL show `1.0`

### Requirement: Leveraged portfolio name suffix
When leverage != 1.0, the result name SHALL include a suffix indicating the leverage factor.

#### Scenario: Name suffix for leveraged result
- **WHEN** leverage=2.0 is applied to a portfolio named "MyPortfolio"
- **THEN** the result name SHALL be "MyPortfolio (2.0x)"

#### Scenario: No suffix for leverage=1.0
- **WHEN** leverage=1.0 (default) is applied
- **THEN** the result name SHALL remain unchanged
