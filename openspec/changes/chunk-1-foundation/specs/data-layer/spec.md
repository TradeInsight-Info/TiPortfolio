## ADDED Requirements

### Requirement: fetch_data returns dict of per-ticker DataFrames
The system SHALL provide `fetch_data(tickers, start, end, source="yfinance")` that returns `dict[str, pd.DataFrame]`. Each DataFrame SHALL have a UTC `DatetimeIndex` and columns: `open`, `high`, `low`, `close`, `volume`.

#### Scenario: Fetch three tickers
- **WHEN** `fetch_data(["QQQ", "BIL", "GLD"], start="2024-01-01", end="2024-01-31")` is called
- **THEN** the returned dict has keys `"QQQ"`, `"BIL"`, `"GLD"`, each mapping to a DataFrame with OHLCV columns and UTC DatetimeIndex

#### Scenario: Single ticker
- **WHEN** `fetch_data(["SPY"], start="2024-01-01", end="2024-01-31")` is called
- **THEN** the returned dict has exactly one key `"SPY"`

### Requirement: validate_data checks index alignment
The system SHALL provide `validate_data(data, extra=None)` that checks all DataFrames share identical DatetimeIndex values. It SHALL raise `ValueError` with the misaligned ticker names if indices differ.

#### Scenario: Aligned data passes
- **WHEN** `validate_data(data)` is called with three DataFrames sharing the same DatetimeIndex
- **THEN** no exception is raised

#### Scenario: Misaligned data raises ValueError
- **WHEN** `validate_data(data)` is called where one DataFrame has a different DatetimeIndex
- **THEN** `ValueError` is raised identifying the misaligned ticker

#### Scenario: Extra data validated alongside main data
- **WHEN** `validate_data(data, extra={"^VIX": vix_df})` is called and VIX has a different index
- **THEN** `ValueError` is raised identifying `"^VIX"` as misaligned
