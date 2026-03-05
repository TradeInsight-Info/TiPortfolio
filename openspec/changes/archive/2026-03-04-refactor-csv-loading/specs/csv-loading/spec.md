## ADDED Requirements

### Requirement: Raw CSV loading without transformation
The `load_csvs` function SHALL load CSV files as raw DataFrames without any data transformation.

#### Scenario: Load single price CSV
- **WHEN** calling `load_csvs` with paths to single price column CSV files
- **THEN** function returns DataFrames with original column structure unchanged

#### Scenario: Load OHLC CSV
- **WHEN** calling `load_csvs` with paths to OHLC format CSV files
- **THEN** function returns DataFrames with original OHLC column structure unchanged

### Requirement: Dedicated OHLC loading function
The `load_price_df` function SHALL be the single source of truth for loading OHLC format CSV files with proper timezone handling.

#### Scenario: Load OHLC with UTC timezone
- **WHEN** calling `load_price_df` with an OHLC CSV file
- **THEN** function returns DataFrame with datetime index parsed as UTC
- **AND** all OHLC columns (open, high, low, close) are preserved

## MODIFIED Requirements

### Requirement: CSV loading interface
The CSV loading functions SHALL provide clear separation of responsibilities between raw loading and format-specific processing.

#### Scenario: Choose appropriate loader
- **WHEN** developer needs to load CSV files
- **THEN** they use `load_csvs` for raw CSV loading without transformation
- **AND** they use `load_price_df` for OHLC format files with timezone handling

#### Scenario: Maintain backward compatibility
- **WHEN** existing code uses `load_price_df`
- **THEN** function behavior remains unchanged
- **AND** all existing functionality is preserved
