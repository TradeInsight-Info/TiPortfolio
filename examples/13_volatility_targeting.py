"""
13 — Volatility Targeting with BasedOnHV
=========================================

Scales a fixed initial allocation up or down so the portfolio's
annualised volatility stays near a target (15%).

When markets are calm, the strategy levers up (sum of weights > 1).
When markets are choppy, it scales down (sum < 1 = cash buffer).

Features demonstrated: Weigh.BasedOnHV, Signal.Monthly
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import pandas as pd

import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

portfolio = ti.Portfolio(
    "vol_target_15pct",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.BasedOnHV(
            initial_ratio={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1},
            target_hv=0.15,  # 15% annualised volatility
            lookback=pd.DateOffset(months=1),
        ),
        ti.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))

print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/13_volatility_targeting.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/13_volatility_targeting.png")
