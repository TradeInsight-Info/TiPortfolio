"""
17 — Full Results: Trades, Metrics, and Charts
===============================================

Demonstrates the full results API on a single backtest:
- full_summary() with extended metrics (Sortino, Calmar, max DD duration, etc.)
- trades property and trades.sample() for inspecting individual trades
- plot_security_weights() for weight evolution over time
- plot_histogram() for return distribution

Features demonstrated: full_summary, Trades, plot_security_weights, plot_histogram
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import pandas as pd

import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

portfolio = ti.Portfolio(
    "equal_weight",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))

# 1. Full summary with extended metrics
print("=== Full Summary ===")
print(result.full_summary())
print()

# 2. Trade records
print(f"=== Total Trades: {len(result[0].trades)} ===")
print()
print("=== Top 3 and Bottom 3 Rebalances (by equity return) ===")
print(result[0].trades.sample(3))
print()

# 3. Security weights chart
import matplotlib
matplotlib.use("Agg")
fig = result[0].plot_security_weights()
fig.savefig("examples/17_security_weights.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/17_security_weights.png")

# 4. Return distribution
fig = result[0].plot_histogram()
fig.savefig("examples/17_histogram.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/17_histogram.png")
