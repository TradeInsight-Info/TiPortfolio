## ADDED Requirements

### Requirement: CSV price data validation

The system SHALL validate that price values in CSV files match close values in corresponding DataFrame CSV files for all supported symbols (BIL, QQQ, GLD).

#### Scenario: BIL CSV data matches DataFrame close values
- **WHEN** bil_2018_2024.csv price column is compared with bil_2018_2024_df.csv close column
- **THEN** all values match exactly

#### Scenario: QQQ CSV data matches DataFrame close values
- **WHEN** qqq_2018_2024.csv price column is compared with qqq_2018_2024_df.csv close column
- **THEN** all values match exactly

#### Scenario: GLD CSV data matches DataFrame close values
- **WHEN** gld_2018_2024.csv price column is compared with gld_2018_2024_df.csv close column
- **THEN** all values match exactly

### Requirement: Automated data validation tests

The system SHALL include automated tests that run during the test suite to verify data consistency between CSV formats.

#### Scenario: Tests pass when data is consistent
- **WHEN** pytest runs data validation tests and CSV data matches
- **THEN** all tests pass without errors

#### Scenario: Tests fail when data is inconsistent
- **WHEN** pytest runs data validation tests and CSV data differs
- **THEN** tests fail with clear error messages indicating the mismatch
