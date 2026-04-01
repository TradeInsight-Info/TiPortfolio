"""
20 — Fetch Live Data: ALLW vs QQQ Long Hold Comparison
======================================================

Demonstrates fetching price data directly from YFinance (no local CSV)
for two tickers: QQQ and ALLW (State Street Bridgewater All Weather ETF).

Builds two buy-and-hold strategies — one for QQQ, one for ALLW — and
compares them side by side over 2025-01-02 to 2026-04-01.

ALLW launched in March 2025, so its pre-listing NaN rows are dropped
automatically. Each Backtest subsets data to its own tickers, so QQQ
starts from January while ALLW starts from March.

Run from the repo root:
    uv run python examples/20_fetch_and_hold.py
"""

from _env import *  # noqa: F403 — load .env

import tiportfolio as ti

# --- Fetch live data per ticker then merge --------------------------------
# ALLW is a new ETF (March 2025) — fetching separately avoids issues with
# YFinance multi-ticker download when one ticker has less history.
data = ti.fetch_data(["QQQ", "ALLW"], start="2025-01-02", end="2026-04-01")



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
print("=== QQQ vs ALLW Long Hold (2025-01-02 → 2026-04-01) ===")
print(result.summary())
print()

fig = result.plot()
fig.savefig("examples/20_fetch_and_hold.png", dpi=150, bbox_inches="tight")
print("Chart saved to examples/20_fetch_and_hold.png")


fig_hist = result.plot_histogram()
fig_hist.savefig("examples/20_fetch_and_hold_histogram.png", dpi=150, bbox_inches="tight")
print("Histogram saved to examples/20_fetch_and_hold_histogram.png")
