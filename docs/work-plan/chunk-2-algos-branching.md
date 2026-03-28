# Chunk 2: More Algos + Branching

**Goal:** Expand the algo catalogue with selection variety, weighting options, and branching combinators.

**Depends on:** Chunk 1

## Deliverable

All `fix-time-rebalance.md` examples work — quarterly rebalance, custom schedule, branching with And/Not, nested composition.

```python
import pandas as pd
import tiportfolio as ti

data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31")

# Quarterly rebalance
portfolio = ti.Portfolio(
    'quarterly',
    [
        ti.Signal.Quarterly(),
        ti.Select.All(),
        ti.Weigh.Ratio(weights={"QQQ": 0.6, "BIL": 0.3, "GLD": 0.1}),
        ti.Action.Rebalance(),
    ],
    ["QQQ", "BIL", "GLD"],
)

result = ti.run(ti.Backtest(portfolio, data))

# Momentum with branching: skip December
portfolio2 = ti.Portfolio(
    'momentum_no_dec',
    [
        ti.And(
            ti.Signal.Monthly(),
            ti.Not(ti.Signal.Schedule(dates=[pd.Timestamp(f"2019-12-01")])),
        ),
        ti.Select.Momentum(n=2, lookback=pd.DateOffset(months=1), lag=pd.DateOffset(days=1)),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    ["QQQ", "BIL", "GLD"],
)
```

## Files to Create / Modify

### New algos

| File | Change |
|------|--------|
| `algos/signal.py` | Add `Signal.Quarterly(months=[2,5,8,11])` |
| `algos/select.py` | Add `Select.Momentum(n, lookback, lag, sort_descending)`, `Select.Filter(condition, data)` |
| `algos/weigh.py` | Add `Weigh.Ratio(weights)`, `Weigh.BasedOnHV(initial_ratio, target_hv, lookback)` |

### Branching combinators

| File | Change |
|------|--------|
| `algo.py` | Add `Or`, `And`, `Not` — all `Algo` subclasses |
| `__init__.py` | Export `Or`, `And`, `Not` at `ti.*` level |

## Spec Sections Covered

- Section 2: Or/And/Not combinators
- Section 5: Signal.Quarterly, Select.Momentum, Select.Filter, Weigh.Ratio, Weigh.BasedOnHV

## Out of Scope

- Signal.VIX → Chunk 3
- Parent/child portfolios → Chunk 3
- Short selling → Chunk 3
- Weigh.BasedOnBeta, Weigh.ERC → Chunk 4
