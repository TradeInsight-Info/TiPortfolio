## Why

The current `Signal.Schedule` only supports `"end"` (month-end) and integer days. Users can't express "first trading day of the month," "mid-month rebalance," weekly schedules, or every-N-period frequencies. These are common rebalancing patterns. Additionally, the `next_trading_day` parameter name doesn't reflect the bidirectional search needed for mid-period targeting.

## What Changes

- **`Signal.Schedule` day expansion**: Accept `"start"` (forward search from day 1), `"mid"` (bidirectional nearest from midpoint), `"end"` (backward search, existing behavior), and `int` (forward search)
- **Param rename**: `next_trading_day` → `closest_trading_day` (default `True`) — **BREAKING** for keyword argument users
- **`Signal.Weekly`**: New class — fires on first/mid/last trading day of each week
- **`Signal.Yearly`**: New class — fires on a specified day in a specified month (default: Dec end)
- **`Signal.EveryNPeriods`**: New class — stateful period counter for biweekly, every-3-months, etc.
- **Propagate rename** through `Signal.Monthly` constructor and examples

## Capabilities

### New Capabilities

- `schedule-day-modes`: `"start"` and `"mid"` day resolution modes for `Signal.Schedule`, with forward and bidirectional trading-day search
- `weekly-signal`: `Signal.Weekly` — fires once per week on configured day
- `yearly-signal`: `Signal.Yearly` — fires once per year on configured month/day
- `every-n-periods-signal`: `Signal.EveryNPeriods` — stateful N-period frequency signal

### Modified Capabilities

- `quarterly-signal`: Rename `next_trading_day` → `closest_trading_day` in `Schedule` propagates to `Monthly` and `Quarterly` constructors

## Impact

- **Breaking**: `next_trading_day` keyword renamed to `closest_trading_day` — any user code using `Signal.Schedule(next_trading_day=False)` or `Signal.Monthly(next_trading_day=False)` must update
- **Code**: 1 source file modified (`signal.py`), 2 test files, examples
- **Dependencies**: None new
