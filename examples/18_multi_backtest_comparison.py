"""
18 — Multi-Backtest Comparison
==============================

Run two strategies side by side and compare:
- summary() for quick comparison
- full_summary() for detailed metrics
- plot() for overlaid equity curves

Strategy 1: Equal-weight monthly rebalance
Strategy 2: QQQ-heavy ratio (70/20/10) monthly rebalance

Features demonstrated: ti.run(bt1, bt2), side-by-side summary, overlaid plot
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

p1 = ti.Portfolio(
    "equal_weight",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    tickers,
)

p2 = ti.Portfolio(
    "heavy_qqq",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.Ratio(weights={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1}),
        ti.Action.Rebalance(),
    ],
    tickers,
)

# Run both backtests together
result = ti.run(ti.Backtest(p1, data), ti.Backtest(p2, data))

# 1. Side-by-side summary
print("=== Summary Comparison ===")
print(result.summary())
print()

# 2. Full summary comparison
print("=== Full Summary Comparison ===")
print(result.full_summary())
print()

# 3. Overlaid equity curves
import matplotlib
matplotlib.use("Agg")
fig = result.plot()
fig.savefig("examples/18_comparison.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/18_comparison.png")

# 4. Overlaid return distributions
fig = result.plot_histogram()
fig.savefig("examples/18_histogram_comparison.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/18_histogram_comparison.png")
