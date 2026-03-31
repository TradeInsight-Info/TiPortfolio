"""
07 — Long Hold: QQQ Only (2018–2024)
=====================================

A pure buy-and-hold of QQQ from 2018-01-01 to 2024-12-31.

Buys QQQ on the very first trading day and holds with no rebalancing.
Signal.Once() fires True exactly once, so the portfolio never trades again
after the initial purchase — capturing the full QQQ bull run across six years.

Useful as a benchmark to see what "just hold Nasdaq-100" looks like
over a period that includes the 2020 COVID crash, 2022 bear market,
and 2023–2024 recovery.
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import tiportfolio as ti

data = ti.fetch_data(["QQQ"], start="2018-01-01", end="2024-12-31", csv=CSV_DATA)

portfolio = ti.Portfolio(
    "qqq_long_hold",
    [
        ti.Signal.Once(),      # buy once on day 1, never trade again
        ti.Select.All(),
        ti.Weigh.Equally(),    # 100% QQQ (single asset)
        ti.Action.Rebalance(),
    ],
    ["QQQ"],
)

result = ti.run(ti.Backtest(portfolio, data))

print("=== QQQ Long Hold (2018-01-01 → 2024-12-31) ===")
print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/07_qqq_long_hold.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/07_qqq_long_hold.png")
