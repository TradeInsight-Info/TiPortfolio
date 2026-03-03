## ADDED Requirements

### Requirement: Composite filter for combining multiple rebalance triggers
The system SHALL provide a CompositeFilter class that combines multiple filters using AND/OR logic.

#### Scenario: AND operator requires all filters to pass
- **WHEN** user creates CompositeFilter(filters=[filter1, filter2], operator="and") and filter1 returns True but filter2 returns False
- **THEN** composite filter returns False (rebalance blocked)

#### Scenario: AND operator allows rebalance when all pass
- **WHEN** user creates CompositeFilter(filters=[filter1, filter2], operator="and") and both filters return True
- **THEN** composite filter returns True (rebalance allowed)

#### Scenario: OR operator allows rebalance when any filter passes
- **WHEN** user creates CompositeFilter(filters=[filter1, filter2], operator="or") and filter1 returns True but filter2 returns False
- **THEN** composite filter returns True (rebalance allowed)

#### Scenario: OR operator blocks when all filters fail
- **WHEN** user creates CompositeFilter(filters=[filter1, filter2], operator="or") and both filters return False
- **THEN** composite filter returns False (rebalance blocked)

#### Scenario: Default operator is AND
- **WHEN** user creates CompositeFilter(filters=[filter1, filter2]) without specifying operator
- **THEN** system uses "and" as default operator

#### Scenario: Empty filter list handling
- **WHEN** user creates CompositeFilter(filters=[])
- **THEN** system raises ValueError with descriptive message

#### Scenario: Invalid operator handling
- **WHEN** user creates CompositeFilter(filters=[filter1], operator="invalid")
- **THEN** system raises ValueError with descriptive message

#### Scenario: Combining VIX and time-based filters
- **WHEN** user creates CompositeFilter(filters=[VixChangeFilter(delta_abs=10), TimeBasedFilter(freezing_time_days=7)], operator="and")
- **THEN** rebalance only occurs when VIX changes significantly AND at least 7 days have passed

#### Scenario: Multiple time-based filters
- **WHEN** user creates CompositeFilter(filters=[TimeBasedFilter(freezing_time_days=5), TimeBasedFilter(freezing_time_days=10)], operator="or")
- **THEN** rebalance occurs when either 5-day OR 10-day freezing period has expired

#### Scenario: Engine integration with composite filter
- **WHEN** user runs any engine with CompositeFilter as rebalance_filter
- **THEN** engine correctly evaluates all filters and applies composite logic

#### Scenario: Backward compatibility with single filters
- **WHEN** existing code uses single filter (VixChangeFilter) as rebalance_filter
- **THEN** all existing functionality continues to work unchanged
