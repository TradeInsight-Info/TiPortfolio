## Why

Implement missing rebalance trigger mechanisms from dimension 1 document to support more flexible portfolio rebalancing strategies, enabling users to configure schedules like weekly days and "never" rebalance, plus volatility-based triggers with freezing periods.

## What Changes

- Add new scheduled rebalance frequencies: weekly Monday, Wednesday, Friday, and "never" (no rebalance).
- Enhance volatility-based rebalance with freezing time parameter to prevent rebalancing too frequently.
- Refactor BacktestEngine to be abstract base class for better extensibility while maintaining shared initialization logic.

## Capabilities

### New Capabilities
- rebalance-triggers: Support for additional scheduled and volatility-based rebalance triggers.

### Modified Capabilities
- backtest-engine: Made abstract with shared initialization logic.

## Impact

- calendar.py: Add new schedule types to VALID_SCHEDULES and get_rebalance_dates function.
- engine.py: Make BacktestEngine abstract, add freezing time support to VolatilityBasedEngine.
- Tests: Update or add tests for new schedules and freezing time.
- Documentation: Update docs/dimensions/dimension 1 trigger of rebalance.md to reflect implemented features.
