"""
14 — Dollar-Neutral Strategy (Long/Short)
==========================================

A parent portfolio with two children:
- Long leg: top-2 momentum winners, equal weight
- Short leg: bottom-2 momentum losers, equal negative weight

The parent allocates 50% capital to each leg. Net market exposure
is roughly zero (dollar-neutral).

Features demonstrated: Parent/child tree, Select.Momentum,
                       Weigh.Equally(short=True), nested portfolios
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import pandas as pd

import tiportfolio as ti

tickers = ["QQQ", "AAPL", "BIL", "GLD"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

lookback = pd.DateOffset(months=1)
lag = pd.DateOffset(days=1)

long = ti.Portfolio(
    "long",
    [
        ti.Select.Momentum(n=2, lookback=lookback, lag=lag, sort_descending=True),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    tickers,
)

short = ti.Portfolio(
    "short",
    [
        ti.Select.Momentum(n=2, lookback=lookback, lag=lag, sort_descending=False),
        ti.Weigh.Equally(short=True),
        ti.Action.Rebalance(),
    ],
    tickers,
)

dollar_neutral = ti.Portfolio(
    "dollar_neutral",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    [long, short],
)

result = ti.run(ti.Backtest(dollar_neutral, data))

print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/14_dollar_neutral.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/14_dollar_neutral.png")
