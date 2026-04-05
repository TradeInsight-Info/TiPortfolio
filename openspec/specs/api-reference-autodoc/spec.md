# Spec: api-reference-autodoc

## Purpose

Provide an auto-generated API reference page using mkdocstrings `:::` directives while preserving the existing hand-written API documentation.

## Requirements

### Requirement: Auto-generated API reference page
A `docs/api/reference.md` page SHALL use mkdocstrings `:::` directives to auto-render docstrings for all public modules.

#### Scenario: Reference page renders public API
- **WHEN** `mkdocs build` completes
- **THEN** `docs/api/reference.md` SHALL render documentation for: Portfolio, Backtest, run, TiConfig, fetch_data, Signal (all subclasses), Select (all subclasses), Weigh (all subclasses), Action (all subclasses), BacktestResult

#### Scenario: Reference page organized by category
- **WHEN** a user opens the reference page
- **THEN** it SHALL be organized into sections: Core, Data, Signals, Selection, Weighting, Actions, Results

### Requirement: Hand-written API docs preserved
The existing `docs/api/index.md` SHALL remain unchanged.

#### Scenario: Existing API page untouched
- **WHEN** the change is applied
- **THEN** `docs/api/index.md` SHALL have no modifications
