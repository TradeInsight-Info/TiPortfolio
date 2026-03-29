## ADDED Requirements

### Requirement: Signal.Once fires exactly once
The system SHALL provide `Signal.Once()` that returns `True` on the first call and `False` on all subsequent calls.

#### Scenario: First call returns True
- **WHEN** Signal.Once() is called for the first time
- **THEN** it returns `True`

#### Scenario: Second and subsequent calls return False
- **WHEN** Signal.Once() is called after the first call
- **THEN** it returns `False`

#### Scenario: Buy-and-hold pattern
- **WHEN** Signal.Once() is used in a portfolio algo stack over 20 trading days
- **THEN** the algo queue fires exactly once (on the first bar), buying positions that are then held
