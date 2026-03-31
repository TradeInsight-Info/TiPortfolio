## ADDED Requirements

### Requirement: Partial CSV validation for dict mode

When `fetch_data` is called with `csv=` as a dict, it SHALL validate that every ticker in the `tickers` list has a corresponding key in the dict before loading any files. If any tickers are missing, it SHALL raise `FileNotFoundError` listing all missing tickers in a single error message.

#### Scenario: All tickers present in csv dict
- **WHEN** `fetch_data(["QQQ", "BIL"], csv={"QQQ": "q.csv", "BIL": "b.csv"})` is called
- **THEN** files SHALL be loaded normally without error

#### Scenario: One ticker missing from csv dict
- **WHEN** `fetch_data(["QQQ", "BIL", "GLD"], csv={"QQQ": "q.csv", "BIL": "b.csv"})` is called
- **THEN** a `FileNotFoundError` SHALL be raised with message containing "GLD"

#### Scenario: Multiple tickers missing from csv dict
- **WHEN** `fetch_data(["QQQ", "BIL", "GLD"], csv={"QQQ": "q.csv"})` is called
- **THEN** a `FileNotFoundError` SHALL be raised listing both "BIL" and "GLD"

### Requirement: Partial CSV validation for directory mode

When `fetch_data` is called with `csv=` as a directory path string, it SHALL check that every ticker in the `tickers` list has a discoverable CSV file in the directory before loading any files. If any tickers are missing, it SHALL raise `FileNotFoundError` listing all missing tickers in a single error message.

#### Scenario: All tickers found in directory
- **WHEN** `fetch_data(["QQQ", "BIL"], csv="/path/to/dir")` is called and `QQQ.csv` and `BIL.csv` exist
- **THEN** files SHALL be loaded normally without error

#### Scenario: Some tickers missing from directory
- **WHEN** `fetch_data(["QQQ", "BIL", "MISSING"], csv="/path/to/dir")` is called and `MISSING.csv` does not exist
- **THEN** a `FileNotFoundError` SHALL be raised with message containing "MISSING"

### Requirement: Quick Start example documents csv parameter

The Quick Start example (`examples/01_quick_start.py`) SHALL include a comment or docstring explaining:
- `csv=` parameter enables offline/faster testing using local CSV files
- Without `csv=`, `fetch_data` requires network access to download data

#### Scenario: Quick Start documents csv support
- **WHEN** a user reads `examples/01_quick_start.py`
- **THEN** they SHALL see documentation about the `csv=` parameter and its offline benefit

### Requirement: Examples use csv parameter for offline data

All example scripts in `examples/` SHALL pass a `csv=` dict parameter to `fetch_data` pointing to CSV files in `tests/data/`. Examples SHALL only use tickers for which CSV files exist.

#### Scenario: Example runs offline
- **WHEN** any example script is run without network access but with CSV files present
- **THEN** the script SHALL complete without network errors

### Requirement: E2E tests use csv parameter instead of mocks

E2E tests SHALL use `fetch_data(csv=...)` with real CSV fixture data instead of patching `_query_yfinance`.

#### Scenario: E2E test runs without mocking
- **WHEN** `test_e2e.py` is run
- **THEN** tests SHALL pass using CSV data without any `unittest.mock.patch` on data functions
