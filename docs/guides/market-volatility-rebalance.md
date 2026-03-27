## Market Volatility Rebalance Example

In the [fix-time-rebalance](./fix-time-rebalance.md) examples, we showed fixed-schedule triggers. Here we use VIX as a regime signal to switch between two different allocation portfolios dynamically.

This uses the [Tree Structure](https://pmorissette.github.io/bt/tree.html) concept from `bt`: a **parent portfolio** holds child portfolios as its `children`. Signal algos select which child receives capital each period.


### How the Tree Execution Works

When a portfolio's `children` are other `Portfolio` objects (not ticker strings), the engine evaluates it as a **parent node**:

1. The parent's algo stack runs first
2. A signal algo (e.g. `VixSignal`) sets `context.selected_child`
3. The engine automatically routes 100% of capital to `selected_child` and evaluates it with a fresh context

Child portfolios **do not need a schedule algo** — the parent controls when evaluation happens. Children just describe *how* to allocate when they are active.


### VIX Regime-Switching Example

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")
vix_data = ti.fetch_data(["^VIX"], start="2019-01-01", end="2024-12-31")

# Child: low-volatility regime — growth-heavy allocation
low_vol_portfolio = ti.Portfolio(
    'low_vol',
    [
        ti.Select.All(),
        ti.Weigh.Ratio(weights={"QQQ": 0.8, "BIL": 0.15, "GLD": 0.05}),
        ti.Action.Rebalance(),
    ],
    tickers,
)

# Child: high-volatility regime — defensive allocation
high_vol_portfolio = ti.Portfolio(
    'high_vol',
    [
        ti.Select.All(),
        ti.Weigh.Ratio(weights={"QQQ": 0.5, "BIL": 0.4, "GLD": 0.1}),
        ti.Action.Rebalance(),
    ],
    tickers,
)

# Parent: uses VIX to route capital to the right child each month
portfolio = ti.Portfolio(
    'vix_based_rebalance',
    [
        ti.Schedule.Monthly(),
        ti.VixSignal(high=30, low=20, signal=vix_data),
        # engine automatically routes capital to selected_child
    ],
    [low_vol_portfolio, high_vol_portfolio],
)

result = ti.run(ti.Backtest(portfolio, data))
result.plot()
result.plot_security_weights()  # clearly shows regime transitions
```

> **VIX threshold behaviour:** When VIX > `high` (30), `high_vol_portfolio` is selected. When VIX < `low` (20), `low_vol_portfolio` is selected. When VIX is **between** the two thresholds, the **previous selection persists** — no flip-flopping in the transition zone. This hysteresis prevents excessive switching during choppy markets.
