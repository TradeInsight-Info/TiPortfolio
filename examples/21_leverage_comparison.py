"""
21 — Leverage Comparison: Same Strategy at 1x, 1.5x, 2x
========================================================

Compare the same monthly-rebalanced QQQ/BIL/GLD portfolio at different
leverage levels using the ``leverage`` parameter in ``ti.run()``.

Leverage is applied post-simulation by scaling daily returns and deducting
a borrowing cost of ``(leverage - 1) * loan_rate / bars_per_year`` per day,
consistent with the engine's carry-cost logic.

Offline mode
------------
Uses ``csv=`` for offline-friendly runs.
"""

from _env import CSV_DATA

import tiportfolio as ti

# 1. Fetch data
data = ti.fetch_data(
    ["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31", csv=CSV_DATA
)

# 2. Define a monthly start-of-month rebalance at 70/20/10
tickers = ["QQQ", "BIL", "GLD"]
weights = {"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1}
algos = [
    ti.Signal.Monthly(day="start"),
    ti.Select.All(),
    ti.Weigh.Ratio(weights),
    ti.Action.Rebalance(),
]

# 3. Create three identical backtests (leverage applied post-run)
bt_1x = ti.Backtest(ti.Portfolio("QBG_1x", list(algos), tickers), data)
bt_15x = ti.Backtest(ti.Portfolio("QBG_1.5x", list(algos), tickers), data)
bt_2x = ti.Backtest(ti.Portfolio("QBG_2x", list(algos), tickers), data)

# 4. Run with different leverage levels
result = ti.run(bt_1x, bt_15x, bt_2x, leverage=[1.0, 1.5, 2.0])

# 5. Compare
print("=== Leverage Comparison ===")
print(result.summary())
print()

# 6. Plot
fig = result.plot()
fig.savefig("examples/21_leverage_comparison.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/21_leverage_comparison.png")
