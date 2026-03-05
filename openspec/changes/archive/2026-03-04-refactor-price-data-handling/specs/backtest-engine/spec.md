## MODIFIED Requirements

### Requirement: BacktestEngine price data format

The BacktestEngine SHALL accept price_dfs as a dictionary where each value is a pandas DataFrame containing OHLC price columns ('open', 'high', 'low', 'close') and an optional 'volume' column.

#### Scenario: DataFrame with OHLC columns accepted
- **WHEN** price_dfs contains DataFrames with required OHLC columns
- **THEN** BacktestEngine initialization succeeds without error

#### Scenario: Missing OHLC columns raises error
- **WHEN** price_dfs contains DataFrame missing any OHLC column
- **THEN** ValueError is raised with clear message about missing columns

### Requirement: Price DataFrame index normalization

The BacktestEngine SHALL normalize DataFrame indices to ensure they are timezone-aware datetime indices with NYSE timezone and 00:00:00 time component.

#### Scenario: Index normalized on initialization
- **WHEN** DataFrame index lacks timezone information
- **THEN** index is converted to datetime with 'America/New_York' timezone and time set to 00:00:00

#### Scenario: Already normalized index unchanged
- **WHEN** DataFrame index is already timezone-aware with correct format
- **THEN** index remains unchanged
