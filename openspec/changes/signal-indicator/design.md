## Context

All current Signal algos are stateless calendar checks except `Signal.VIX` which reads external data and has hysteresis state. `Signal.Indicator` follows the `VIX` pattern — stateful, reads price data, returns True on specific conditions — but generalised to any user-defined condition with edge detection.

The algo pipeline calls every algo on every bar. The engine passes the **full** price DataFrame in `context.prices` (not truncated to date), so the algo must correctly bound its `.loc` slice — same pattern as `Weigh.BasedOnHV` and `Select.Momentum`.

## Goals / Non-Goals

**Goals:**
- Enable TA-based signal generation (SMA cross, RSI threshold breach, etc.)
- Detect state *transitions* (crossovers), not static states
- Composable with existing Signal algos via `Or`/`And`

**Non-Goals:**
- Built-in indicator library (SMA, EMA, RSI, etc.) — the user provides the condition function
- Multi-ticker conditions (e.g., pairs trading) — one ticker per Indicator instance; use `Or`/`And` for multi-ticker logic
- Handling "rebalance only if weights changed" optimisation — separate concern

## Decisions

### 1. Condition function signature: `Callable[[pd.Series], bool]`

The condition receives a `pd.Series` of close prices (DatetimeIndex, float values) over the lookback window. It returns a boolean **state** — True means "condition met" (e.g., SMA50 > SMA200).

**Alternative considered**: `Callable[[pd.DataFrame], bool]` (full OHLCV) → rejected because most TA indicators only need close prices, and users can always pass a lambda that ignores extra columns. Keeping it as Series simplifies the common case.

**Alternative considered**: Pass returns instead of prices → rejected because SMA/EMA operate on price levels, not returns.

### 2. Edge detection via `_prev_state` instance variable

```
__call__ flow:
┌──────────────────────────────────────────────────────────────┐
│  1. Slice prices: context.prices[ticker].loc[start:end]      │
│  2. Call condition(close_prices) → current_state (bool)       │
│  3. Compare with self._prev_state                             │
│  4. Update self._prev_state = current_state                   │
│  5. Return True only if transition matches self._cross        │
└──────────────────────────────────────────────────────────────┘
```

This follows the same stateful pattern as `Signal.VIX._active` and `Signal.EveryNPeriods._counter`.

### 3. `ticker` parameter instead of operating on all context.prices

The condition function evaluates a single ticker's prices. This is explicit and avoids ambiguity about which ticker to check. For multi-ticker TA signals, compose multiple Indicators:

```python
Or(
    Signal.Indicator(ticker="QQQ", condition=sma_cross, ...),
    Signal.Indicator(ticker="SPY", condition=sma_cross, ...),
)
```

### 4. Validate `cross` parameter in `__init__`

Raise `ValueError` on invalid values rather than silently ignoring. Accepted values: `"up"`, `"down"`, `"both"`.

## Risks / Trade-offs

- **[Performance]** Condition function is called on every bar → If the user's condition is expensive (e.g., computing 200-day SMA from scratch each time), this could slow backtest. Mitigation: users can cache/precompute indicators outside the algo. Pandas `.rolling().mean()` is efficient.
- **[Statefulness across backtests]** `_prev_state` persists across bars but would need resetting if the same algo instance were reused across backtests → Currently not an issue because the engine creates fresh Context per run, but the algo instance is shared. Mitigation: initialise `_prev_state = None` in `__init__`, reset logic is in first-bar handling.
- **[Ticker not in context.prices]** If the specified ticker isn't in the price data → Return False (don't fire). Log a warning on first occurrence.
