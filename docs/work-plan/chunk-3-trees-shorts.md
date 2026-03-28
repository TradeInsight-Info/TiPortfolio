# Chunk 3: Tree Portfolios + Short Selling

**Goal:** Enable parent/child portfolio trees, VIX regime switching, and short positions.

**Depends on:** Chunk 2

## Deliverable

Dollar-neutral strategy (`allocation-strategies.md`), VIX regime-switching (`market-volatility-rebalance.md`), and extra-data.md examples all work.

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]
data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")
vix_data = ti.fetch_data(["^VIX"], start="2019-01-01", end="2024-12-31")

# Child portfolios
low_vol = ti.Portfolio('low_vol', [
    ti.Select.All(),
    ti.Weigh.Ratio(weights={"QQQ": 0.8, "BIL": 0.15, "GLD": 0.05}),
    ti.Action.Rebalance(),
], tickers)

high_vol = ti.Portfolio('high_vol', [
    ti.Select.All(),
    ti.Weigh.Ratio(weights={"QQQ": 0.5, "BIL": 0.4, "GLD": 0.1}),
    ti.Action.Rebalance(),
], tickers)

# Parent portfolio with VIX regime switching
portfolio = ti.Portfolio('vix_regime', [
    ti.Signal.Monthly(),
    ti.Signal.VIX(high=30, low=20, data=vix_data),
    ti.Action.Rebalance(),
], [low_vol, high_vol])

result = ti.run(ti.Backtest(portfolio, data))
```

## Files to Create / Modify

### Parent/child engine

| File | Change |
|------|--------|
| `backtest.py` | Add parent path to `evaluate_node` (is_parent detection, recursion into children). Add `allocate_equity_to_children` (4-step equity redistribution). Add `_liquidate_child`. Update `mark_to_market` for parent nodes (equity = sum of children). |
| `portfolio.py` | No structural change — Portfolio already holds `children: list[str] \| list[Portfolio]` |

### New algos

| File | Change |
|------|--------|
| `algos/signal.py` | Add `Signal.VIX(high, low, data)` — hysteresis regime switching, lazy `_active` init |
| `algos/weigh.py` | Add `Weigh.Equally(short=True)` support — negative equal weights for short leg |

### Short selling

| File | Change |
|------|--------|
| `backtest.py` | Add daily carry costs: `loan_rate` for leveraged longs, `stock_borrow_rate` for shorts. Support negative `positions` quantities and negative weights in `execute_leaf_trades`. |

## Spec Sections Covered

- Section 4: Parent equity allocation, child liquidation, mark-to-market (parent path), daily carry costs
- Section 5: Signal.VIX, Weigh.Equally(short=True)

## Key Design Decisions (from spec)

- **Parent cash invariant:** Parent nodes always have `cash = 0.0`. On child liquidation, recovered proceeds are stored temporarily in `child.equity`, summed into `total_equity`, then redistributed. Never use `portfolio.cash` on parents.
- **Signal.VIX children ordering:** `children[0]` = low-vol regime (VIX < low), `children[1]` = high-vol regime (VIX > high). Hysteresis: when VIX is between thresholds, previous selection persists.
- **Action.Rebalance handles both paths:** Checks `isinstance(children[0], Portfolio)` to dispatch to `_allocate_children` (parent) or `_execute_leaf` (leaf). `evaluate_node` does NOT call callbacks directly — only handles child recursion.

## Out of Scope

- Weigh.BasedOnBeta, Weigh.ERC → Chunk 4
