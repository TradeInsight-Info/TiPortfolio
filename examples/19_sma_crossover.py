"""
19 — SMA Crossover: Technical Analysis Signal
==============================================

Uses Signal.Indicator to trigger rebalancing on 50/200 SMA crossovers.

Strategy logic:
- Golden cross (SMA50 crosses above SMA200) → go 100% QQQ
- Death cross  (SMA50 crosses below SMA200) → go 100% BIL (cash proxy)
- No crossover → hold current position

This requires two pieces working together:
1. **Signal.Indicator(cross="both")** — fires on ANY state transition (up or down)
2. **SMAWeigh** — a custom Algo that checks the current SMA state to decide
   whether to allocate to QQQ (bullish) or BIL (bearish)

Since Signal.Indicator only fires on crossovers, the Weigh step only runs
on cross bars. At that moment, the current SMA state tells us which
direction we just crossed.

Offline mode
------------
Uses ``csv=`` for offline data. Remove it for live data (requires network).
"""

from _env import CSV_DATA  # noqa: F401 — load .env + CSV paths

import pandas as pd

import tiportfolio as ti
from tiportfolio.algo import Algo, Context


# ---------------------------------------------------------------------------
# 1. Define the SMA state condition
# ---------------------------------------------------------------------------
# Returns boolean STATE (not a crossover).
# Signal.Indicator detects the state TRANSITION for us.

def sma_bullish(close: pd.Series) -> bool:  # type: ignore[type-arg]
    """True when 50-day SMA is above 200-day SMA."""
    if len(close) < 200:
        return False
    sma_50 = close.rolling(50).mean().iloc[-1]
    sma_200 = close.rolling(200).mean().iloc[-1]
    return bool(sma_50 > sma_200)


# ---------------------------------------------------------------------------
# 2. Custom Weigh algo — sets weights based on current SMA regime
# ---------------------------------------------------------------------------
# TODO: Implement the __call__ method below.
#
# This algo runs only when Signal.Indicator fires (on a crossover bar).
# At that moment, check whether SMA(50) > SMA(200) for the ticker:
#   - If bullish (SMA50 > SMA200): set context.weights = {"QQQ": 1.0, "BIL": 0.0}
#   - If bearish (SMA50 < SMA200): set context.weights = {"QQQ": 0.0, "BIL": 1.0}
#
# You have access to:
#   - context.prices["QQQ"].loc[start:end, "close"]  → price series
#   - context.date → current bar date
#
# Trade-off to consider: should you recompute SMAs here, or is there a way
# to share state with the condition function? (Hint: recomputing is simpler
# and keeps algos independent — the performance cost is negligible.)

class SMAWeigh(Algo):
    """Allocate 100% to QQQ when bullish, 100% to BIL when bearish."""

    def __init__(self, ticker: str, lookback: pd.DateOffset) -> None:
        self._ticker = ticker
        self._lookback = lookback

    def __call__(self, context: Context) -> bool:
        start = context.date - self._lookback
        end = context.date
        close = context.prices[self._ticker].loc[start:end, "close"]

        if sma_bullish(close):
            context.weights = {"QQQ": 1.0, "BIL": 0.0}
        else:
            context.weights = {"QQQ": 0.0, "BIL": 1.0}

        return True


# ---------------------------------------------------------------------------
# 3. Fetch data
# ---------------------------------------------------------------------------
data = ti.fetch_data(
    ["QQQ", "BIL"], start="2019-01-01", end="2024-12-31", csv=CSV_DATA
)

# ---------------------------------------------------------------------------
# 4. Build portfolio
# ---------------------------------------------------------------------------
# Signal fires on ANY SMA crossover (up or down).
# SMAWeigh then checks current state to decide allocation direction.
portfolio = ti.Portfolio(
    "sma_crossover",
    [
        ti.Signal.Indicator(
            ticker="QQQ",
            condition=sma_bullish,
            lookback=pd.DateOffset(days=365),
            cross="both",  # fire on golden cross AND death cross
        ),
        ti.Select.All(),
        SMAWeigh(ticker="QQQ", lookback=pd.DateOffset(days=365)),
        ti.Action.Rebalance(),
    ],
    ["QQQ", "BIL"],
)

# ---------------------------------------------------------------------------
# 5. Run and display results
# ---------------------------------------------------------------------------
result = ti.run(ti.Backtest(portfolio, data))

print(result.summary())

# 6. Save charts
fig = result.plot()
fig.savefig("examples/19_sma_crossover.png", dpi=150, bbox_inches="tight")
print("\nChart saved to examples/19_sma_crossover.png")

fig_weights = result.plot_security_weights()
fig_weights.savefig("examples/19_sma_crossover_weights.png", dpi=150, bbox_inches="tight")
print("Weights chart saved to examples/19_sma_crossover_weights.png")
