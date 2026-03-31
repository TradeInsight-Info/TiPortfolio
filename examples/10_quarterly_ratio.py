"""
10 — Quarterly Rebalance with Fixed Ratio Weights
==================================================

Rebalances every quarter (Jan, Apr, Jul, Oct) using explicit fixed weights
instead of equal weighting. QQQ gets the lion's share, with BIL and GLD
as lower-risk stabilisers.

Features demonstrated: Signal.Quarterly, Weigh.Ratio
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

portfolio = ti.Portfolio(
    "quarterly_ratio",
    [
        ti.Signal.Quarterly(),
        ti.Select.All(),
        ti.Weigh.Ratio(weights={"QQQ": 0.6, "BIL": 0.3, "GLD": 0.1}),
        ti.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))

print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/10_quarterly_ratio.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/10_quarterly_ratio.png")
