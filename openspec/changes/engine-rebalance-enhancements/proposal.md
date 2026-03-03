## Why

The current rebalance engine implementation lacks key schedule options and has an unintuitive freezing time mechanism that doesn't match the Dimension 1 requirements. Users need weekly rebalancing patterns, a "never" option for buy-and-hold strategies, and clearer time-based freezing controls.

## What Changes

- Add weekly schedule patterns (Monday, Wednesday, Friday, Mon-Wed-Fri) to the Schedule class
- Add "never" schedule option for buy-and-hold strategies
- Create TimeBasedFilter class for explicit freezing time periods
- Add CompositeFilter for combining multiple rebalance triggers
- Improve API clarity with better parameter names and documentation
- Maintain full backward compatibility with existing VixChangeFilter behavior

## Capabilities

### New Capabilities
- `weekly-schedules`: Weekly rebalancing patterns including individual days and combined patterns
- `never-schedule`: Buy-and-hold option with no rebalancing
- `time-based-filter`: Explicit freezing time periods independent of VIX changes
- `composite-filter`: Combine multiple rebalance triggers with AND/OR logic

### Modified Capabilities
- No existing capability requirements are changing - this is purely additive

## Impact

- **Code affected**: `src/tiportfolio/calendar.py`, `src/tiportfolio/allocation.py`, `src/tiportfolio/engine.py`, `src/tiportfolio/backtest.py`
- **API changes**: New schedule options and filter classes, existing APIs unchanged
- **Dependencies**: No new external dependencies required
- **Systems**: Enhanced rebalance engine with more flexible scheduling options
- **Testing**: Additional test coverage for new schedule patterns and filter combinations
