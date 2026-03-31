"""
09 — ERC (Risk Parity): Equal Risk Contribution
================================================

Sizes each asset so every position contributes the same amount of risk
to the total portfolio. Uses Ledoit-Wolf covariance shrinkage and
riskfolio-lib's CCD solver. Weights always sum to 1.0 (fully invested).
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import pandas as pd

import tiportfolio as ti

tickers = ["QQQ", "AAPL", "GLD", "BIL"]

data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

portfolio = ti.Portfolio(
    "erc_monthly",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.ERC(
            lookback=pd.DateOffset(months=3),
            covar_method="ledoit-wolf",
            risk_parity_method="ccd",
        ),
        ti.Action.Rebalance(),
    ],
    tickers,
)

result = ti.run(ti.Backtest(portfolio, data))

print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/09_erc_risk_parity.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/09_erc_risk_parity.png")
