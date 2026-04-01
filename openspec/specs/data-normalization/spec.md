# Data Normalization

## Purpose

Provides a shared internal helper for normalizing per-ticker DataFrames with consistent handling of column names, timezone conversions, sorting, and data cleaning.

## Requirements

### Requirement: Shared ticker DataFrame normalization
The system SHALL provide a single internal helper `_normalize_ticker_df(df, default_tz)` that normalizes a per-ticker DataFrame by: lowercasing column names, converting the DatetimeIndex to UTC (localizing from `default_tz` if tz-naive), sorting by index, and dropping all-NaN rows.

#### Scenario: Normalize tz-naive DataFrame from yfinance
- **WHEN** `_normalize_ticker_df` receives a DataFrame with tz-naive index and `default_tz="US/Eastern"`
- **THEN** the returned DataFrame SHALL have columns lowercased, index localized to US/Eastern then converted to UTC, sorted by index, with all-NaN rows removed

#### Scenario: Normalize tz-aware DataFrame
- **WHEN** `_normalize_ticker_df` receives a DataFrame with a tz-aware index (any timezone)
- **THEN** the returned DataFrame SHALL have index converted to UTC without re-localizing

#### Scenario: Normalize CSV-loaded DataFrame
- **WHEN** `_normalize_ticker_df` receives a DataFrame with tz-naive index and `default_tz="UTC"`
- **THEN** the returned DataFrame SHALL have index localized directly to UTC

### Requirement: _load_from_csv uses shared normalization
The `_load_from_csv` function SHALL delegate column/tz/sort/dropna logic to `_normalize_ticker_df` with `default_tz="UTC"`.

#### Scenario: CSV loading produces same output after refactor
- **WHEN** a CSV file is loaded via `_load_from_csv`
- **THEN** the resulting DataFrame SHALL be identical to the output before the refactor (lowercase columns, UTC index, sorted)

### Requirement: _split_flat_to_dict uses shared normalization
The `_split_flat_to_dict` function SHALL delegate column/tz/sort/dropna logic to `_normalize_ticker_df` with `default_tz="US/Eastern"`.

#### Scenario: YFinance data produces same output after refactor
- **WHEN** a flat DataFrame from yfinance is split via `_split_flat_to_dict`
- **THEN** the resulting per-ticker DataFrames SHALL be identical to the output before the refactor
