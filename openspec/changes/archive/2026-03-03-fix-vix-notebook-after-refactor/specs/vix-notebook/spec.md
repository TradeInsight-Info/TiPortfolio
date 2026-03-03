## ADDED Requirements

### Requirement: VIX notebook compatibility with refactored API
The system SHALL ensure the VIX target rebalance notebook works with the refactored volatility engine API.

#### Scenario: VixRegimeAllocation constructor fix
- **WHEN** notebook creates VixRegimeAllocation instance
- **THEN** constructor SHALL only require high_vol_allocation and low_vol_allocation parameters
- **AND** SHALL NOT require target_vix, lower_bound, upper_bound parameters

#### Scenario: VIX parameters in engine call
- **WHEN** notebook calls VolatilityBasedEngine.run()
- **THEN** call SHALL include target_vix, lower_bound, upper_bound parameters
- **AND** parameters SHALL be passed correctly to the engine

#### Scenario: Notebook execution success
- **WHEN** all notebook cells are executed sequentially
- **THEN** notebook SHALL complete without errors
- **AND** SHALL produce VIX regime strategy results
- **AND** SHALL generate comparison charts with long-hold QQQ strategy

### Requirement: API change documentation
The system SHALL document the API change for future reference.

#### Scenario: Constructor change documentation
- **WHEN** notebook is viewed by users
- **THEN** comments SHALL explain VIX parameters moved from VixRegimeAllocation to VolatilityBasedEngine
- **AND** SHALL show the before/after API usage

#### Scenario: Migration guidance
- **WHEN** users need to update similar code
- **THEN** notebook comments SHALL provide clear migration pattern
- **AND** SHALL explain the separation of concerns introduced by refactor
