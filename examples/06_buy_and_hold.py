"""
06 — Buy and Hold: No Rebalancing
==================================

A pure buy-and-hold strategy: buy QQQ, BIL, and GLD on the first
trading day (equal weight), then hold forever with no rebalancing.

Uses Signal.Once() which fires True exactly once — on the first bar.
After the initial purchase, the algo queue never fires again,
so positions drift naturally with the market.

Compare this to 01_quick_start.py (monthly rebalance) to see
the effect of rebalancing vs letting winners run.
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import tiportfolio as ti

data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

portfolio = ti.Portfolio(
    "buy_and_hold",
    [
        ti.Signal.Once(),          # fire only on the first bar
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    ["QQQ", "BIL", "GLD"],
)

result = ti.run(ti.Backtest(portfolio, data))

print("=== Buy-and-Hold QQQ/BIL/GLD (no rebalancing) ===")
print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/06_buy_and_hold.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/06_buy_and_hold.png")
