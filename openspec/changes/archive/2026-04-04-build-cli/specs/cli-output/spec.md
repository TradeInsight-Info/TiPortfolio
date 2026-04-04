## ADDED Requirements

### Requirement: Default output is summary
By default, the CLI SHALL print the backtest summary table to stdout.

#### Scenario: Default summary output
- **WHEN** a backtest completes without `--full`
- **THEN** `result.summary()` SHALL be printed

### Requirement: Full summary flag
`--full` SHALL print the extended summary.

#### Scenario: Full summary
- **WHEN** `--full` is passed
- **THEN** `result.full_summary()` SHALL be printed instead of `summary()`

### Requirement: Plot flag
`--plot <path>` SHALL save the equity curve chart to the specified file.

#### Scenario: Save plot
- **WHEN** `--plot output.png` is passed
- **THEN** `result.plot()` SHALL be saved to `output.png`

#### Scenario: No plot by default
- **WHEN** `--plot` is not passed
- **THEN** no chart file SHALL be created

### Requirement: Leverage flag
`--leverage` SHALL accept a single float or a comma-separated list of floats for post-simulation leverage.

#### Scenario: Single leverage applied
- **WHEN** `--leverage 1.5` is passed
- **THEN** `run(bt, leverage=1.5)` SHALL be called

#### Scenario: Leverage list applied
- **WHEN** `--leverage 1.0,1.5,2.0` is passed
- **THEN** three identical backtests SHALL be created and `run(bt1, bt2, bt3, leverage=[1.0, 1.5, 2.0])` SHALL be called, enabling side-by-side leverage comparison

#### Scenario: Default leverage
- **WHEN** `--leverage` is not specified
- **THEN** leverage SHALL default to `1.0`
