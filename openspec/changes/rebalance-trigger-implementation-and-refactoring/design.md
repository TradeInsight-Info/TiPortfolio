## Context

The current TiPortfolio library supports basic scheduled rebalances (monthly, quarterly, yearly variants) and a VIX-based regime rebalance. The dimension 1 document specifies additional trigger mechanisms including weekly schedules (Monday, Wednesday, Friday), a "never" rebalance option, and volatility-based rebalancing with freezing periods. The BacktestEngine class is concrete but has subclasses that override the run method, suggesting a need for abstraction to better share common logic while allowing customization.

## Goals / Non-Goals

**Goals:**
- Implement new rebalance schedules: weekly Monday, Wednesday, Friday, and "never"
- Add freezing time support to volatility-based rebalances to prevent overly frequent rebalancing
- Refactor BacktestEngine to be abstract base class with shared initialization logic
- Maintain backward compatibility with existing engine usage

**Non-Goals:**
- Complex trigger combinations (as noted as struck-through in the document)
- Changes to allocation strategies or data fetching mechanisms
- Performance optimizations beyond current implementation

## Decisions

**Schedule Implementation:**
- Add "weekly_monday", "weekly_wednesday", "weekly_friday", "never" to VALID_SCHEDULES
- For weekly schedules, use pandas date_range with 'W-MON' etc. frequencies, aligned to trading days
- If Monday market is closed, use Tuesday
- For "never", return empty DatetimeIndex from get_rebalance_dates

**Freezing Time in Volatility Engine:**
- Add freezing_days parameter (default 0) to VolatilityBasedEngine.__init__
- Store last_rebalance_date and check time delta in rebalance logic
- Use rebalance_filter callable to implement the freezing check

**Engine Abstraction:**
- Import ABC from abc module
- Make BacktestEngine inherit from ABC
- Add @abstractmethod decorator to run method
- Keep __init__ as shared initialization logic

**Alternatives Considered:**
- For schedules: Custom date generation vs pandas freq - chose pandas for consistency
- For freezing: Modify Schedule class vs engine parameter - chose engine parameter for flexibility

## Risks / Trade-offs

**Risk:** New schedules may increase computation for date alignment
**Mitigation:** Limit to reasonable frequencies, reuse existing closest_nyse_trading_day logic

**Risk:** Freezing time adds state management complexity
**Mitigation:** Keep implementation simple, default to 0 (no freezing)

