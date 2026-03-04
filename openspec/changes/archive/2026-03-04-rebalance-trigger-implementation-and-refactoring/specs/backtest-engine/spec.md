## MODIFIED Requirements

### Requirement: Abstract BacktestEngine base class
The BacktestEngine SHALL be an abstract base class that cannot be instantiated directly, with shared initialization logic for subclasses.

#### Scenario: Direct instantiation raises error
- **WHEN** user attempts to instantiate BacktestEngine directly
- **THEN** TypeError is raised indicating it's an abstract class

#### Scenario: Subclasses inherit initialization
- **WHEN** a subclass of BacktestEngine is instantiated
- **THEN** the shared __init__ method sets allocation, rebalance, fee_per_share, initial_value, and risk_free_rate attributes correctly
