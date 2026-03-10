# Design: Fix Signal-Based Rebalance Look-Ahead Bias

## Context

The backtest engine has a look-ahead bias: signal-based strategies observe day T's close data (VIX level, prices for vol/beta computation, position values) and execute trades at day T's close prices simultaneously. This is unrealistic — in practice, you observe close data after market close and can only act the next trading day. The bias is present across two layers: rebalance scheduling (VIX regime) and allocation weight computation (VolatilityTargeting, BetaNeutral, DollarNeutral).

## Goals

- **Eliminate look-ahead bias** for all signal-based rebalance paths: VIX regime dates, VIX change filter, and dynamic allocation strategies.
- **Configurable signal delay** with a default of 1 trading day, so users can model different execution assumptions.
- **Preserve calendar-based behavior** — month_end, weekly, quarter, etc. schedules are unaffected (no signal dependency).
- **Backward-compatible API** — existing code continues to work without changes, but produces corrected (bias-free) results by default.

## Non-Goals

- Modeling intraday execution (e.g., next-day open price). We use close-to-close throughout.
- Adding slippage or market impact models — orthogonal concern.
- Fixing the pre-existing mypy type errors in engine.py/backtest.py.

## Decisions

### D1: Signal delay via shifted rebalance dates (not execution delay)

**Approach**: When a signal fires on day T, shift the resulting rebalance date to T+N (where N = `signal_delay`, default 1). This keeps the backtest loop simple — it still executes on rebalance dates at that day's close prices — but the dates themselves are shifted.

**Alternative considered**: Adding an "execution delay" inside `run_backtest()` where trades are queued and executed N days later. Rejected because it complicates the loop (pending orders, partial fills) for no practical benefit over date-shifting.

**Where the shift happens**:

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Rebalance date generation (calendar.py)        │
│                                                          │
│  _vix_regime_rebalance_dates():                         │
│    VIX crosses threshold on day T                        │
│    → rebalance_date = trading_dates[idx_of_T + delay]   │
│                                                          │
│ Layer 2: Rebalance filter (engine.py)                   │
│                                                          │
│  VixChangeFilter fires on day T                          │
│    → defer rebalance to T + delay trading days           │
│                                                          │
│ Layer 3: prices_history window (backtest.py)             │
│                                                          │
│  On rebalance day T+1:                                   │
│    signal_date = T  (execution_date - delay)             │
│    prices_history = prices_df.loc[:signal_date]          │
│    execution prices = prices_df.loc[execution_date]      │
└─────────────────────────────────────────────────────────┘
```

### D2: prices_history sliced to signal date, not execution date

On execution day T+1, the allocation strategy receives `prices_history=prices_df.loc[:T]` (the signal date) — not `prices_df.loc[:T+1]`. This ensures weight computations (rolling vol, rolling beta, position imbalance) use only information available at the time the signal was generated.

The `prices_row` argument (used for trade execution) remains `prices_df.loc[T+1]` — the execution day's close prices.

```
Signal day (T):      prices_history endpoint ──┐
                                                │
Execution day (T+1): prices_row for trades ────│──┐
                                                │  │
Timeline: ... T-2  T-1  T  T+1  T+2 ...       │  │
                         ▲   ▲                  │  │
                         │   └── execute here ──┘  │
                         └── observe signal ───────┘
```

### D3: DollarNeutral tolerance check uses signal-day positions

DollarNeutral is unique: it computes an imbalance ratio from `positions_dollars` and decides whether to rebalance *within* `get_target_weights`. With the delay, positions on execution day T+1 have already drifted from the signal day T. The tolerance check should use T's positions (from `prices_history`) to decide, then execute at T+1 prices if triggered.

Implementation: Pass `signal_date` in context so DollarNeutral can reconstruct T's position values from prices_history for the tolerance check, while still receiving T+1's `positions_dollars` for the actual weight computation.

### D4: signal_delay parameter threading

```
Engine.run(signal_delay=1)
  │
  ├─► get_rebalance_dates(..., signal_delay=1)      # calendar.py
  │     └─► shifts VIX regime dates by +1
  │
  ├─► VixChangeFilter (in engine.py wrapper)
  │     └─► engine defers execution by signal_delay
  │
  └─► run_backtest(signal_delay=1, ...)              # backtest.py
        └─► on rebalance: signal_date = date - delay
              prices_history = prices_df.loc[:signal_date]
```

The parameter is added to:
- `BacktestEngine.__init__()` (stored as instance attribute)
- `run_backtest()` function signature
- `get_rebalance_dates()` for VIX regime path
- `VolatilityBasedEngine` wrapper logic for rebalance_filter

Default value: `1` (one trading day delay). Value `0` reproduces legacy behavior.

### D5: No legacy_mode flag

Rather than a boolean `legacy_mode`, use `signal_delay=0` to reproduce old behavior. This is more transparent and generalizable. Documentation should note the behavior change.

## Risks and Trade-offs

| Risk | Mitigation |
|------|------------|
| Existing backtests produce different results | Expected and correct. Document in changelog. `signal_delay=0` preserves old behavior. |
| Edge case: signal on last trading day, T+1 is out of range | Discard rebalance if shifted date falls outside trading_dates range. |
| Performance: computing signal_date lookback in the loop | Negligible — just an index offset, no additional data fetching. |
| DollarNeutral tolerance check complexity | Keep it simple: pass signal_date in context, let strategy use prices_history for threshold check. |
| VIX regime + freezing_days interaction | Freezing is applied after date generation, so shifted dates are frozen correctly. No special handling needed. |
