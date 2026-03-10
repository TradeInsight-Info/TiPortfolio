# Fix Signal-Based Rebalance Look-Ahead Bias

## Why

All signal-based strategies in the backtest engine suffer from look-ahead bias: they observe day T's close prices to generate a rebalancing signal and simultaneously execute trades at those same day T close prices. In real trading, you cannot observe the close and act on it at the same instant. This bias systematically flatters strategy performance, particularly for VIX-regime switching (where VIX and equities are strongly inversely correlated intraday), and produces unreliable backtest results for VolatilityTargeting, BetaNeutral, and DollarNeutral strategies.

## What Changes

Introduce a configurable **signal delay** (default: 1 trading day) so that signals observed on day T trigger trade execution on day T+1. This affects two layers:

1. **Rebalance scheduling** (VIX regime / VIX change filter): When VIX crosses a threshold on day T, the rebalance date becomes T+1 instead of T.
2. **Allocation signal window** (`prices_history`): When computing weights on rebalance day T+1, the prices_history passed to strategies should use `prices_df.loc[:T]` (signal day) for weight computation, while execution occurs at T+1's close prices. Alternatively, the lookback window is shifted by 1 day so that the most recent observation informing the signal is T (the prior close), not T+1.

Calendar-based schedules (month_end, weekly, etc.) remain unchanged - their rebalance dates are known in advance and carry no signal bias.

## Capabilities

### Modified
- **backtest-engine**: Add `signal_delay` parameter to `run_backtest()`. Shift signal window vs execution bar.
- **rebalance-triggers**: VIX regime and VIX change filter shift rebalance dates forward by `signal_delay` trading days.
- **strategy-history-context**: `prices_history` sliced to signal day (T), not execution day (T+1).
- **volatility-targeting**: No code change needed - bias fix is upstream in backtest loop.
- **beta-neutral**: No code change needed - bias fix is upstream in backtest loop.
- **dollar-neutral**: Tolerance check uses T's mark-to-market; execution at T+1. May need adjustment.

### New
- None. This is a correctness fix to existing behavior.

## Impact

- **All existing VIX-based backtests will produce different (less favorable) results.** This is expected and correct.
- **Signal-based allocation strategies** (VolTarget, BetaNeutral, DollarNeutral) will show slightly different performance when used on calendar schedules, because their lookback window no longer includes the execution bar.
- **FixRatio and calendar-only strategies are unaffected.**
- **Breaking change**: Default behavior changes. Consider a `legacy_mode=True` flag to preserve old behavior during transition, or simply document the change.
