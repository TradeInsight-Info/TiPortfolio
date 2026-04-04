## ADDED Requirements

### Requirement: Tickers are required
`--tickers` SHALL be a required option accepting a comma-separated list of ticker symbols.

#### Scenario: Tickers provided
- **WHEN** `--tickers QQQ,BIL,GLD` is passed
- **THEN** tickers `["QQQ", "BIL", "GLD"]` SHALL be used for fetch_data and Portfolio construction

#### Scenario: Missing tickers
- **WHEN** `--tickers` is not provided
- **THEN** an error SHALL indicate tickers are required

### Requirement: Date range is required
`--start` and `--end` SHALL be required options in YYYY-MM-DD format.

#### Scenario: Date range provided
- **WHEN** `--start 2019-01-01 --end 2024-12-31` is passed
- **THEN** fetch_data SHALL use those dates

#### Scenario: Missing date range
- **WHEN** `--start` or `--end` is not provided
- **THEN** an error SHALL indicate the missing option

### Requirement: Data source option
`--source` SHALL accept `yfinance` (default) or `alpaca`.

#### Scenario: Default source
- **WHEN** `--source` is not specified
- **THEN** fetch_data SHALL use `source="yfinance"`

### Requirement: CSV offline mode
`--csv` SHALL accept a directory path for offline CSV data.

#### Scenario: CSV directory
- **WHEN** `--csv ./tests/data/` is passed
- **THEN** fetch_data SHALL use the csv parameter with files from that directory

### Requirement: Config overrides
`--capital`, `--fee`, and `--rf` SHALL override TiConfig defaults.

#### Scenario: Custom capital
- **WHEN** `--capital 50000` is passed
- **THEN** TiConfig SHALL use `initial_capital=50000`

#### Scenario: Custom fee
- **WHEN** `--fee 0.01` is passed
- **THEN** TiConfig SHALL use `fee_per_share=0.01`

#### Scenario: Default config
- **WHEN** no config flags are passed
- **THEN** TiConfig defaults SHALL be used
