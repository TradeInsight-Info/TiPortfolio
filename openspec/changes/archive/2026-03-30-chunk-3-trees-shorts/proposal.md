## Why

Chunk 2 completed the algo catalogue (signals, selectors, weighting). But portfolios are still flat — no parent/child capital allocation, no VIX regime switching, and short positions have no borrow/loan costs. Without tree support, dollar-neutral strategies and regime-switching strategies from the guides can't run. Without carry costs, short-selling backtests overstate returns.

## What Changes

- **Recursive mark-to-market**: Parent equity = sum of children equity, computed recursively
- **Parent equity allocation**: 4-step redistribution — liquidate deselected children, compute total, redistribute by weights, zero deselected
- **Child liquidation**: Sell all positions, accumulate proceeds net of fees
- **`_allocate_children` callback**: Wired into engine context so `Action.Rebalance` works on parent nodes
- **`Signal.VIX`**: Hysteresis regime switching; writes directly to `context.selected` and `context.weights`
- **Daily carry costs**: Short borrow cost + leverage loan cost, deducted every bar
- **Fractional shares**: `execute_leaf_trades` updated from `math.floor` to division (matching spec)
- **Parent portfolio initialisation**: Recursive init of children when root is a parent

## Capabilities

### New Capabilities

- `parent-child-engine`: Recursive mark-to-market, parent equity allocation, child liquidation, and recursive portfolio initialisation
- `vix-signal`: `Signal.VIX` with hysteresis regime switching between two child portfolios
- `daily-carry-costs`: Short borrow cost (`stock_borrow_rate`) and leverage loan cost (`loan_rate`) deducted daily

### Modified Capabilities

- `schedule-day-modes`: No change (Signal.VIX is independent of scheduling)

## Impact

- **Code**: `backtest.py` is the primary modification (new functions + loop changes); `signal.py` gets one new class
- **Breaking**: `execute_leaf_trades` switches from integer to fractional shares — changes trade quantities slightly
- **Dependencies**: None new
- **Risk**: Engine-level changes affect all backtests — thorough regression testing required
