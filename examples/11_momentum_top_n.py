"""
11 — Momentum Selection: Top-N by Recent Return
================================================

Each month, ranks tickers by their trailing 1-month return and selects
the top 2 performers. Equal-weight rebalancing into the winners.

Features demonstrated: Select.Momentum, Signal.Monthly, Weigh.Equally
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import pandas as pd

import tiportfolio as ti

tickers = ["QQQ", "AAPL", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

portfolio = ti.Portfolio(
    "momentum_top2",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Select.Momentum(
            n=2,
            lookback=pd.DateOffset(months=1),
            lag=pd.DateOffset(days=1),
            sort_descending=True,
        ),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))

print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/11_momentum_top_n.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/11_momentum_top_n.png")
