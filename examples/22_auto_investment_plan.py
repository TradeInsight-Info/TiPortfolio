"""
22 — Auto Investment Plan (AIP / Dollar-Cost Averaging)
=======================================================

Simulate contributing $1,000 every month into a 3-ETF equal-weight portfolio.
This mirrors a real-world savings plan where you invest a fixed amount
at regular intervals regardless of market conditions.

The ``run_aip`` function works exactly like ``run`` but injects cash on the
last trading day of each month before the algo stack fires.

Offline mode
------------
This example uses ``csv=`` to load data from local CSV files for faster,
offline-friendly runs.  The ``CSV_DATA`` dict in ``_env.py`` maps tickers
to pre-downloaded YFinance CSVs in ``tests/data/``.

To fetch live data instead, remove the ``csv=`` parameter — this requires
network access.
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import tiportfolio as ti

# 1. Fetch data (offline via CSV)
data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

# 2. Define the strategy
portfolio = ti.Portfolio(
    "aip_equal_weight",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    ["QQQ", "BIL", "GLD"],
)

# 3. Run AIP backtest — $1,000 added every month
result = ti.run_aip(ti.Backtest(portfolio, data), monthly_aip_amount=1000)

# 4. View results (includes total_contributions and contribution_count)
print(result.summary())
print()

# 5. Compare: lump-sum vs AIP
result_lump = ti.run(ti.Backtest(portfolio, data))
print("Lump-sum final value:", result_lump.summary().loc["final_value", "value"])
print("AIP final value:     ", result.summary().loc["final_value", "value"])
print("AIP contributions:   ", result.summary().loc["total_contributions", "value"])
print()

# 6. Save equity curve chart
fig = result.plot()
fig.savefig("examples/22_auto_investment_plan.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/22_auto_investment_plan.png")
