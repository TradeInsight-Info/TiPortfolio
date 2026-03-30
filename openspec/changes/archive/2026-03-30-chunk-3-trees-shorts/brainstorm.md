# Chunk 3: Tree Portfolios + Short Selling

**Goal**: Enable parent/child portfolio trees with capital allocation, VIX regime switching, daily carry costs for short positions, and recursive mark-to-market.

**Architecture**: Engine-level changes to `backtest.py` — add `allocate_equity_to_children`, `_liquidate_child`, recursive `mark_to_market`, and `deduct_daily_carry_costs`. One new signal class (`Signal.VIX`). No changes to algo abstractions or portfolio data model.

**Tech Stack**: Python 3.12, pandas, pandas-market-calendars

**Spec**: `docs/superpowers/specs/2026-03-28-core-engine-implementation-design.md` — Sections 3, 4, 5

## File Map

1. Modify: `src/tiportfolio/backtest.py` — Add `allocate_equity_to_children`, `_liquidate_child`, recursive `mark_to_market`, `deduct_daily_carry_costs`; wire `_allocate_children` callback in `_run_single`; initialise parent portfolios recursively
2. Modify: `src/tiportfolio/algos/signal.py` — Add `Signal.VIX`
3. Create: `tests/test_tree.py` — Parent/child portfolio tests (capital allocation, child liquidation, recursive mark-to-market)
4. Create: `tests/test_carry_costs.py` — Daily carry cost tests (short borrow, leverage loan)
5. Modify: `tests/test_signal.py` — Add `Signal.VIX` tests
6. Modify: `tests/test_backtest.py` — Update `execute_leaf_trades` tests for fractional shares (spec uses division, not floor)
7. Modify: `tests/test_e2e.py` — Add parent/child integration test

## Chunks

### Chunk A: Recursive Mark-to-Market + Parent Initialisation

Make `mark_to_market` recursive (parent equity = sum of children equity). Initialise parent and child portfolios correctly in `_run_single`.

Key design:
- Parent: `cash=0.0`, `positions={}`, `equity=initial_capital`
- Children: initialised on first `allocate_equity_to_children` call, not at engine start
- `mark_to_market` checks `is_leaf` → leaf formula or recursive sum

Files:
- `src/tiportfolio/backtest.py`
- `tests/test_tree.py`

Steps:
- Refactor `mark_to_market` to handle both leaf and parent nodes recursively
- Update `_run_single` to detect parent portfolio and initialise accordingly
- Add tests: parent equity = sum of children, recursive depth > 1

### Chunk B: Parent Equity Allocation + Child Liquidation

Implement `allocate_equity_to_children` (4-step equity redistribution) and `_liquidate_child`. Wire `_allocate_children` callback into `_run_single` context.

Key design from spec:
1. Liquidate deselected children → store recovered proceeds in `child.equity`
2. Compute `total_equity = sum(c.equity for c in portfolio.children)`
3. Redistribute to selected children: `child.equity = total_equity * fraction`
4. Zero deselected children completely

Parent cash invariant: `portfolio.cash = 0.0` always for parent nodes.

Files:
- `src/tiportfolio/backtest.py`
- `tests/test_tree.py`

Steps:
- Implement `_liquidate_child` — sell all positions, accumulate proceeds in `child.cash`
- Implement `allocate_equity_to_children` — 4-step redistribution
- Wire `_allocate_children=allocate_equity_to_children` in `_run_single` context
- Add tests: capital splits correctly, deselected child zeroed, liquidation fee deducted

### Chunk C: Signal.VIX (Regime Switching)

Implement `Signal.VIX` with hysteresis. It writes to `context.selected` and `context.weights` directly — no special engine path needed.

Key design:
- `children[0]` = low-vol regime (VIX < low), `children[1]` = high-vol regime (VIX > high)
- Between thresholds: hysteresis, previous selection persists
- Lazy init: `_active` defaults to `children[0]` on first call
- Writes `context.selected = [self._active]` and `context.weights = {self._active.name: 1.0}`

Files:
- `src/tiportfolio/algos/signal.py`
- `tests/test_signal.py`

Steps:
- Implement `Signal.VIX` class
- Add tests: below low → children[0], above high → children[1], hysteresis between thresholds, lazy init

### Chunk D: Daily Carry Costs

Implement `deduct_daily_carry_costs` — applied every bar after mark-to-market, before algo evaluation.

Key design from spec:
- Short borrow: `abs(qty * price) * stock_borrow_rate / bars_per_year` for negative qty
- Leverage loan: `(long_value - equity) * loan_rate / bars_per_year` when long exposure > equity
- Recursive for parent nodes
- Deducted from `portfolio.cash`

Files:
- `src/tiportfolio/backtest.py`
- `tests/test_carry_costs.py`

Steps:
- Implement `deduct_daily_carry_costs` (leaf + recursive parent path)
- Integrate into `_run_single` loop between mark-to-market and algo evaluation
- Add tests: short position deducts borrow cost, leveraged long deducts loan cost, no cost when unleveraged

### Chunk E: Execute Leaf Trades Update

The spec uses `delta_value / price` (fractional shares) rather than `math.floor`. Update `execute_leaf_trades` to match spec.

Files:
- `src/tiportfolio/backtest.py`
- `tests/test_backtest.py`

Steps:
- Replace `math.floor(target_value / price)` with `target_value / price` for fractional shares
- Update `execute_leaf_trades` to use `delta_qty * price` cost formula from spec
- Update affected tests
