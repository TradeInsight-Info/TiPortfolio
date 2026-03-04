# Purpose

Standardize all datetime handling in TiPortfolio to UTC timezone for consistent, DST-free operations.

## Requirements

### Requirement: Datetime indices normalized to UTC

All pandas DataFrame datetime indices SHALL be converted to UTC timezone during data processing to ensure consistent time references regardless of data source timezone.

#### Scenario: Naive datetime converted to UTC
- **WHEN** DataFrame has naive datetime index (no timezone information)
- **THEN** index is localized to UTC timezone

#### Scenario: Existing timezone converted to UTC
- **WHEN** DataFrame has datetime index in any timezone other than UTC
- **THEN** index is converted to UTC timezone

#### Scenario: UTC timezone preserved
- **WHEN** DataFrame has datetime index already in UTC timezone
- **THEN** index remains in UTC timezone unchanged
