## Context

The TiPortfolio library currently supports monthly, quarterly, and yearly rebalancing schedules, plus VIX-based volatility rebalancing. However, the Dimension 1 requirements specify weekly patterns and a clearer freezing time mechanism. The current VixChangeFilter combines VIX change detection with time-based freezing in an unintuitive way. Users need explicit weekly schedules and a "never" option for buy-and-hold strategies.

The existing architecture is well-structured with separate engines (BacktestEngine, ScheduleBasedEngine, VolatilityBasedEngine) and a flexible allocation system. The calendar module handles schedule generation, while the allocation module provides filtering capabilities.

## Goals / Non-Goals

**Goals:**
- Add weekly schedule patterns (Monday, Wednesday, Friday, Mon-Wed-Fri) without breaking existing functionality
- Implement explicit time-based freezing that's independent of VIX change detection
- Provide a "never" schedule option for buy-and-hold strategies
- Enable combining multiple rebalance triggers (e.g., VIX changes + time-based freezing)
- Maintain full backward compatibility with existing APIs

**Non-Goals:**
- Changing the core backtest engine architecture
- Modifying existing VixChangeFilter behavior
- Adding external dependencies
- Changing the existing allocation strategy interface

## Decisions

### 1. Weekly Schedule Implementation
**Decision:** Extend the existing VALID_SCHEDULES enum and add weekly date generation functions to calendar.py
**Rationale:** Leverages the existing schedule system architecture, maintains consistency with current patterns, and requires minimal changes to engine code. Alternative approaches (like custom schedule objects) would require larger architectural changes.

### 2. Time-Based Freezing
**Decision:** Create a new TimeBasedFilter class separate from VixChangeFilter
**Rationale:** Separates concerns - VixChangeFilter focuses on market volatility triggers, while TimeBasedFilter handles temporal constraints. This makes the API more intuitive and allows independent use of each filter type.

### 3. Filter Composition
**Decision:** Implement CompositeFilter to combine multiple filters with AND/OR logic
**Rationale:** Allows complex trigger combinations (e.g., "rebalance when VIX changes significantly AND at least 7 days have passed") without cluttering individual filter classes. This pattern is common in event processing systems.

### 4. "Never" Schedule
**Decision:** Add "never" to VALID_SCHEDULES and handle it in get_rebalance_dates by returning empty DatetimeIndex
**Rationale:** Simple implementation that integrates cleanly with existing schedule processing. The backtest engine already handles empty rebalance date sets correctly.

## Risks / Trade-offs

**Risk:** Weekly schedule date generation might conflict with market holidays
**Mitigation:** Use existing closest_nyse_trading_day function to align weekly dates with trading calendar, same as current schedules

**Risk:** CompositeFilter complexity could make debugging difficult
**Mitigation:** Add detailed logging and clear error messages that indicate which filter blocked rebalancing

**Risk:** Performance impact from additional filter processing
**Mitigation:** Filters are simple boolean functions with minimal overhead; performance impact should be negligible compared to portfolio valuation calculations

**Trade-off:** More schedule options increase API surface area
**Justification:** The added flexibility addresses real user needs and follows existing patterns, keeping the API consistent

## Migration Plan

1. **Phase 1:** Add weekly schedules and "never" option to calendar.py
2. **Phase 2:** Implement TimeBasedFilter and CompositeFilter in allocation.py  
3. **Phase 3:** Update engines to support new filter combinations
4. **Phase 4:** Add comprehensive tests and update documentation
5. **Rollback:** All changes are additive; existing functionality remains unchanged

## Open Questions

- Should weekly schedules align to calendar weeks or trading weeks? (Decision: Use trading calendar alignment via existing closest_nyse_trading_day function)
- How should CompositeFilter handle conflicting filter requirements? (Decision: Use explicit AND/OR operator, default to AND)
- Should TimeBasedFilter use business days or calendar days for freezing periods? (Decision: Use calendar days for simplicity, document this clearly)
