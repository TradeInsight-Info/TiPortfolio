"""
15 — VIX Regime Switching
=========================

A parent portfolio switches between two child strategies based on VIX:
- VIX < 20 → low_vol child (risk-on: heavy QQQ)
- VIX > 30 → high_vol child (risk-off: heavy BIL + GLD)
- Between 20–30 → hysteresis (stick with current regime)

Features demonstrated: Signal.VIX, parent/child tree, regime switching
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31", csv=CSV_DATA)
vix_data = ti.fetch_data(["^VIX"], start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

low_vol = ti.Portfolio(
    "low_vol",
    [
        ti.Select.All(),
        ti.Weigh.Ratio(weights={"QQQ": 0.8, "BIL": 0.15, "GLD": 0.05}),
        ti.Action.Rebalance(),
    ],
    tickers,
)

high_vol = ti.Portfolio(
    "high_vol",
    [
        ti.Select.All(),
        ti.Weigh.Ratio(weights={"QQQ": 0.5, "BIL": 0.4, "GLD": 0.1}),
        ti.Action.Rebalance(),
    ],
    tickers,
)

portfolio = ti.Portfolio(
    "vix_regime",
    [
        ti.Signal.Monthly(),
        ti.Signal.VIX(high=30, low=20, data=vix_data),
        ti.Action.Rebalance(),
    ],
    [low_vol, high_vol],
)

result = ti.run(ti.Backtest(portfolio, data))

print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/15_vix_regime_switching.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/15_vix_regime_switching.png")
