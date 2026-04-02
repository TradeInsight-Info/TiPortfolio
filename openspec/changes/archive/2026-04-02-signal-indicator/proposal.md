## Why

The current Signal algos are all calendar-based (Monthly, Weekly, Quarterly, EveryNPeriods) or regime-based (VIX). There's no way to trigger rebalancing based on technical analysis indicators like SMA crossovers, RSI thresholds, or MACD signals. Users who want TA-driven strategies must hack `Select.Filter` which only receives single-row data, not the lookback window needed for rolling indicators.

A crossover is an **edge event** (state transition), not a level check. `SMA(50) > SMA(200)` is a status; the *crossing* requires detecting when the previous bar had `SMA(50) < SMA(200)` and the current bar has `SMA(50) > SMA(200)`.

## What Changes

- **New `Signal.Indicator` algo**: Accepts a user-defined condition function that receives a lookback window of close prices and returns a boolean state. The algo detects state *transitions* and fires True only on crossover bars.
- **Configurable cross direction**: `cross="up"` (False→True), `cross="down"` (True→False), or `cross="both"`.
- **Stateful edge detection**: Tracks previous condition state internally; first bar initialises state without firing.

## Capabilities

### New Capabilities
- `signal-indicator`: A new Signal algo that fires on technical indicator state transitions (crossovers/threshold breaches), accepting a user-defined condition function with price lookback

### Modified Capabilities
_(none)_

## Impact

- **Code**: `src/tiportfolio/algos/signal.py` — new `Signal.Indicator` class (~40 lines)
- **Tests**: New `tests/test_signal_indicator.py`
- **API**: New public algo `Signal.Indicator(condition, lookback, cross)` — additive, no breaking changes
- **Dependencies**: None — uses pandas rolling/mean already available
