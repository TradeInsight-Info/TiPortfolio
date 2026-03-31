"""
04 — Single Asset: QQQ Buy-and-Hold
====================================

A single-ticker portfolio is effectively buy-and-hold.
With monthly equal-weight on one asset, the only "rebalance" is
the initial purchase on the first month-end.

This serves as a baseline to compare more complex strategies against.
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import tiportfolio as ti

data = ti.fetch_data(["QQQ"], start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

portfolio = ti.Portfolio(
    "qqq_hold",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    ["QQQ"],
)

result = ti.run(ti.Backtest(portfolio, data))

print("=== QQQ Buy-and-Hold (via Monthly Rebalance) ===")
print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/04_single_asset.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/04_single_asset.png")
