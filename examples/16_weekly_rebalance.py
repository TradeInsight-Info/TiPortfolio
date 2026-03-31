"""
16 — Weekly Rebalance
=====================

Rebalances to equal weight every Friday (end of week). Demonstrates
a higher-frequency rebalancing schedule compared to the usual monthly.

Features demonstrated: Signal.Weekly
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

portfolio = ti.Portfolio(
    "weekly_equal",
    [
        ti.Signal.Weekly(day="end"),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))

print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/16_weekly_rebalance.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/16_weekly_rebalance.png")
