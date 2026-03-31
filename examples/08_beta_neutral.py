"""
08 — Beta Neutral: Target Zero Market Beta
===========================================

Scales initial weights iteratively so the portfolio's beta to AAPL is ~0.
High-beta assets get scaled down; low/negative-beta assets get scaled up.
Weights are NOT normalised — sum(w) < 1 implies a cash residual.
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import pandas as pd

import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31", csv=CSV_DATA)
aapl_data = ti.fetch_data(["AAPL"], start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

portfolio = ti.Portfolio(
    "beta_neutral",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.BasedOnBeta(
            initial_ratio={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1},
            target_beta=0,
            lookback=pd.DateOffset(months=1),
            base_data=aapl_data["AAPL"],
        ),
        ti.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))

print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/08_beta_neutral.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/08_beta_neutral.png")
