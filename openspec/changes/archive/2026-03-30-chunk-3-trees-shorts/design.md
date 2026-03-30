## Context

The engine currently only supports leaf portfolios — `_run_single` initialises one flat portfolio and sets `_execute_leaf` but not `_allocate_children`. The recursive structure in `_evaluate_node` exists (detects parents, recurses into children) but `Action.Rebalance` raises `RuntimeError` on parents because the callback is `None`. Short selling works mechanically (`Weigh.Equally(short=True)`) but no carry costs are applied.

Key files:
- `src/tiportfolio/backtest.py` — Engine: `_run_single`, `mark_to_market`, `execute_leaf_trades`, `_evaluate_node`
- `src/tiportfolio/algos/signal.py` — Signal classes (adding VIX)
- `src/tiportfolio/algos/rebalance.py` — `Action.Rebalance` (dispatches to `_execute_leaf` or `_allocate_children`)
- `src/tiportfolio/portfolio.py` — Portfolio (no changes needed)
- `src/tiportfolio/config.py` — TiConfig has `loan_rate`, `stock_borrow_rate` already declared

## Goals / Non-Goals

**Goals:**
- Recursive `mark_to_market` (parent = sum of children)
- `allocate_equity_to_children` with 4-step redistribution
- `_liquidate_child` for deselected children
- Wire `_allocate_children` callback into context
- `Signal.VIX` with hysteresis
- `deduct_daily_carry_costs` (short borrow + leverage loan)
- Fractional shares in `execute_leaf_trades`
- Recursive portfolio initialisation for parent nodes

**Non-Goals:**
- `Weigh.BasedOnBeta`, `Weigh.ERC` — Chunk 4
- Results/charting changes — Chunk 5
- Custom data sources
- Multi-level parent nesting beyond 2 levels (though the recursive design naturally supports it)

## Decisions

### D1: Parent cash is always 0.0

Parent nodes never hold cash directly. When children are liquidated, the proceeds go to `child.cash` → `child.equity` → summed into `total_equity` → redistributed. This avoids accounting ambiguity about where cash "lives" in a tree.

### D2: Fractional shares replace integer shares

The spec uses `delta_value / price` (fractional), not `math.floor(target_value / price)` (integer). This is a minor breaking change but aligns with the spec. Most backtesting frameworks use fractional shares by default.

### D3: Signal.VIX writes selected + weights directly

Unlike other signals that only return True/False, VIX also writes `context.selected` and `context.weights`. This means it replaces both the Select and Weigh algo in the stack. This is spec-defined behaviour — the parent's algo queue is `[Signal.Monthly(), Signal.VIX(...), Action.Rebalance()]` with no Select or Weigh needed.

### D4: Carry costs are deducted from cash, not equity

Short borrow and leverage loan costs reduce `portfolio.cash` on each bar. The equity impact appears on the next `mark_to_market` call (since equity = cash + positions). This is the standard approach — costs are a cash outflow, not a direct equity adjustment.

### D5: _run_single initialises children recursively

For parent portfolios, `_run_single` must:
1. Set root: `cash=0.0`, `equity=initial_capital`, `positions={}`
2. For each child: `cash=0.0`, `equity=0.0`, `positions={}` (children get equity from first `allocate_equity_to_children` call)

Children are NOT pre-funded with `initial_capital / n` — the parent's algo queue decides allocation.

### D6: execute_leaf_trades closes positions by deletion

When a ticker is in `portfolio.positions` but not in `context.selected`, the position is sold and the key is deleted from the dict. This keeps the positions dict clean — no zero-quantity entries.

## Risks / Trade-offs

**[Risk] Fractional shares changes existing test expectations** → Mitigation: Update affected tests. The change is small (floor → division) and all tests will be explicitly updated.

**[Risk] Recursive mark-to-market performance on deep trees** → Mitigation: In practice, portfolio trees are 2-3 levels deep. Recursion overhead is negligible for backtesting.

**[Risk] Signal.VIX requires VIX data alignment with price data** → Mitigation: `validate_data(data, extra=vix_data)` at `Backtest` construction catches date mismatches early.

**[Risk] Carry cost rounding over many bars** → Mitigation: Use float arithmetic consistently. No rounding is applied — costs accumulate naturally via daily deductions from cash.
