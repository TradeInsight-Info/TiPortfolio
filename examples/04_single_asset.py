"""
04 — Single Asset: SPY Buy-and-Hold
====================================

A single-ticker portfolio is effectively buy-and-hold.
With monthly equal-weight on one asset, the only "rebalance" is
the initial purchase on the first month-end.

This serves as a baseline to compare more complex strategies against.
"""

import _env  # noqa: F401 — load .env before anything else

import tiportfolio as ti

data = ti.fetch_data(["SPY"], start="2019-01-01", end="2024-12-31")

portfolio = ti.Portfolio(
    "spy_hold",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    ["SPY"],
)

result = ti.run(ti.Backtest(portfolio, data))

print("=== SPY Buy-and-Hold (via Monthly Rebalance) ===")
print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/04_single_asset.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/04_single_asset.png")
