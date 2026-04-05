# Spec: docstring-completion

## Purpose

Ensure key public classes and functions have complete Google-style docstrings so that mkdocstrings renders useful, complete API documentation.

## Requirements

### Requirement: Portfolio docstring complete
`Portfolio.__init__` SHALL have a Google-style docstring with Args block documenting `name`, `algos`, and `children`.

#### Scenario: Portfolio Args block present
- **WHEN** mkdocstrings renders Portfolio
- **THEN** constructor parameters SHALL be documented

### Requirement: Backtest docstring complete
`Backtest.__init__` SHALL have a Google-style docstring with Args block documenting `portfolio`, `data`, and `config`.

#### Scenario: Backtest Args block present
- **WHEN** mkdocstrings renders Backtest
- **THEN** constructor parameters SHALL be documented

### Requirement: BacktestResult public methods documented
`BacktestResult.summary()`, `BacktestResult.full_summary()`, `BacktestResult.plot()` SHALL have Google-style docstrings with Returns blocks.

#### Scenario: BacktestResult methods documented
- **WHEN** mkdocstrings renders BacktestResult
- **THEN** public method return types and descriptions SHALL be visible

### Requirement: validate_data docstring complete
`validate_data` SHALL have a Google-style docstring with Args and Raises blocks.

#### Scenario: validate_data documented
- **WHEN** mkdocstrings renders validate_data
- **THEN** parameters and exceptions SHALL be documented
