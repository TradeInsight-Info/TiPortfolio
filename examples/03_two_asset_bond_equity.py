"""
03 — Two-Asset Bond + Equity Split
===================================

A classic diversified portfolio: one equity ETF (SPY) and one bond ETF (TLT),
rebalanced monthly to equal weight (50/50 split).

This is the foundation of the "60/40 portfolio" concept. With equal-weight,
it's a 50/50 split, but the principle is the same: bonds dampen volatility
while equities provide growth. Monthly rebalancing automatically sells
the winner and buys the loser — a disciplined contrarian approach.
"""

import _env  # noqa: F401 — load .env before anything else

import tiportfolio as ti

data = ti.fetch_data(["SPY", "TLT"], start="2019-01-01", end="2024-12-31")

portfolio = ti.Portfolio(
    "bond_equity_5050",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    ["SPY", "TLT"],
)

result = ti.run(ti.Backtest(portfolio, data))

print("=== 50/50 SPY + TLT (Monthly Rebalance) ===")
print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/03_bond_equity.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/03_bond_equity.png")
