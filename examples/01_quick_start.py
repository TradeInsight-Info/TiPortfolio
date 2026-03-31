"""
01 — Quick Start: Monthly Equal-Weight Rebalance
=================================================

The simplest possible backtest: rebalance three ETFs to equal weight
on the last trading day of each month.

This is the Quick Example from the API reference.

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

# 1. Fetch 5 years of daily OHLCV data (offline via CSV)
data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31", csv=CSV_DATA)

# 2. Define the strategy as an algo stack
#    Signal  → WHEN to rebalance (monthly)
#    Select  → WHAT to include (all tickers)
#    Weigh   → HOW MUCH to allocate (equal weight)
#    Action  → EXECUTE the trades
portfolio = ti.Portfolio(
    "equal_weight_monthly",
    [
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    ["QQQ", "BIL", "GLD"],
)

# 3. Run the backtest
result = ti.run(ti.Backtest(portfolio, data))

# 4. View results
print(result.summary())
print()

# 5. Save equity curve chart
fig = result.plot()
fig.savefig("examples/01_quick_start.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/01_quick_start.png")
