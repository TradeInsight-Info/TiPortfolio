> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [x]) syntax for tracking.

## 1. Recursive Mark-to-Market + Parent Initialisation

- [x] 1.1 Refactor `mark_to_market` in `backtest.py` to handle parent nodes (parent equity = sum of children equity, recursive)
- [x] 1.2 Update `_run_single` to detect parent portfolio and initialise: root `cash=0.0`, `equity=initial_capital`, `positions={}`; children `cash=0.0`, `equity=0.0`, `positions={}`
- [x] 1.3 Create `tests/test_tree.py` with tests: parent equity = sum of children, leaf mark-to-market unchanged, parent with zero-equity child
- [x] 1.4 Run tests — all pass

## 2. Parent Equity Allocation + Child Liquidation

- [x] 2.1 Implement `_liquidate_child(child, prices, date, config)` in `backtest.py` — sell all positions, deduct fees, accumulate in `child.cash`
- [x] 2.2 Implement `allocate_equity_to_children(portfolio, context)` in `backtest.py` — 4-step redistribution (liquidate deselected, compute total, redistribute, zero deselected)
- [x] 2.3 Wire `_allocate_children=allocate_equity_to_children` in `_run_single` context creation
- [x] 2.4 Add tests to `test_tree.py`: equal split, deselected child liquidated and zeroed, parent cash invariant (always 0.0), parent runs without RuntimeError
- [x] 2.5 Run tests — all pass

## 3. Signal.VIX

- [x] 3.1 Implement `Signal.VIX` in `signal.py` — hysteresis regime switching, lazy `_active` init, writes `context.selected` + `context.weights`
- [x] 3.2 Add tests to `test_signal.py`: below low → children[0], above high → children[1], hysteresis persists, lazy init defaults to children[0], always returns True
- [x] 3.3 Run tests — all pass

## 4. Daily Carry Costs

- [x] 4.1 Implement `deduct_daily_carry_costs(portfolio, prices, date, config)` in `backtest.py` — short borrow + leverage loan, recursive for parents
- [x] 4.2 Integrate into `_run_single` loop: after mark-to-market, before algo evaluation
- [x] 4.3 Create `tests/test_carry_costs.py` with tests: short borrow cost deducted, leverage loan cost deducted, no cost when unleveraged, recursive for parent/child
- [x] 4.4 Run tests — all pass

## 5. Fractional Shares Update

- [x] 5.1 Update `execute_leaf_trades` in `backtest.py` — replace `math.floor(target_value / price)` with `target_value / price`; update cost formula to match spec
- [x] 5.2 Update affected tests in `test_backtest.py` — adjust expected quantities from integer to fractional
- [x] 5.3 Run tests — all pass

## 6. Integration + E2E

- [x] 6.1 Add parent/child E2E test to `test_e2e.py` — parent with two leaf children, monthly rebalance, verify result summary works
- [x] 6.2 Add VIX regime-switching E2E test — parent with VIX signal and two child portfolios
- [x] 6.3 Run full test suite — all existing + new tests pass
