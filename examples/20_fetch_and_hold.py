"""
20 — Fetch Live Data: ALLW vs QQQ Long Hold Comparison
======================================================

Demonstrates fetching price data directly from YFinance (no local CSV)
for two tickers: QQQ and ALLW (State Street Bridgewater All Weather ETF).

Builds two buy-and-hold strategies — one for QQQ, one for ALLW — and
compares them side by side over 2025-04-01 to 2026-04-01.

ALLW launched in March 2025, so data is fetched per-ticker and merged
to handle any gaps gracefully.

Run from the repo root:
    uv run python examples/20_fetch_and_hold.py
"""

from _env import *  # noqa: F403 — load .env

import tiportfolio as ti

# --- Fetch live data per ticker then merge --------------------------------
# ALLW is a new ETF (March 2025) — fetching separately avoids issues with
# YFinance multi-ticker download when one ticker has less history.
data = ti.fetch_data(["QQQ", "ALLW"], start="2025-03-05", end="2026-04-01")



# --- Buy once, hold forever ------------------------------------------------
# Each portfolio must have its own algo instances — stateful algos like
# Signal.Once() cannot be shared across portfolios.
qqq_hold = ti.Portfolio("qqq_long_hold", [
    ti.Signal.Once(), ti.Select.All(), ti.Weigh.Equally(), ti.Action.Rebalance(),
], ["QQQ"])

allw_hold = ti.Portfolio("allw_long_hold", [
    ti.Signal.Once(), ti.Select.All(), ti.Weigh.Equally(), ti.Action.Rebalance(),
], ["ALLW"])

# --- Run both backtests together for side-by-side comparison -------------
result = ti.run(
    ti.Backtest(qqq_hold, data),
    ti.Backtest(allw_hold, data),
)

# --- Output --------------------------------------------------------------
print("=== QQQ vs ALLW Long Hold (2025-04-01 → 2026-04-01) ===")
print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/20_fetch_and_hold.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/20_fetch_and_hold.png")
