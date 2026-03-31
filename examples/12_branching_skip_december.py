"""
12 — Branching: Skip December Rebalance
========================================

Monthly rebalance, but skip December — for example, to avoid
tax-loss harvesting season or year-end illiquidity.

Uses And/Not combinators to compose: "monthly AND NOT December".

Features demonstrated: ti.And, ti.Not, Signal.Schedule(month=12)
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

portfolio = ti.Portfolio(
    "no_december",
    [
        ti.And(
            ti.Signal.Monthly(),
            ti.Not(ti.Signal.Schedule(month=12)),
        ),
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
fig.savefig("examples/12_branching_skip_december.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/12_branching_skip_december.png")
