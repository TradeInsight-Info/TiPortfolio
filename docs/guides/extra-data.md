## Using Extra Data

Some algos need data beyond asset prices — VIX for regime detection, macro indicators for filtering, or any external time series. This guide explains how to fetch, prepare, and pass extra data to algos that use it.


### The Rule: Extra Data Must Share the Same Time Index

Extra data must have the **same date index and timezone as your price data**. If the indices don't align bar-by-bar, the engine cannot safely look up values at each rebalance date.

Use `ti.fetch_data` to fetch extra data the same way you fetch prices — it normalises timestamps to UTC and applies the same calendar alignment:

```python
import tiportfolio as ti

# price data
tickers = ["QQQ", "BIL", "GLD"]
data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")

# extra data — same date range, same call
vix_data = ti.fetch_data(["^VIX"], start="2019-01-01", end="2024-12-31")
```

If you bring your own DataFrame (CSV, database, etc.), align it before use:

```python
import pandas as pd

# load your own series
macro = pd.read_csv("macro.csv", index_col=0, parse_dates=True)

# align to price data index — forward-fill gaps, drop dates outside range
macro = macro.reindex(data["QQQ"].index, method="ffill").dropna()
```

> **Why forward-fill?** Macro data (e.g. monthly CPI releases) updates less frequently than daily prices. `ffill` carries the last known value forward, which is what you'd observe in live trading. Never back-fill — that introduces lookahead bias.


### Passing Extra Data to an Algo

Algos that require extra data accept it as a constructor argument. The algo receives the full DataFrame; it slices to the current bar internally.

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]
data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")
vix_data = ti.fetch_data(["^VIX"], start="2019-01-01", end="2024-12-31")

portfolio = ti.Portfolio(
    'vix_regime',
    [
        ti.Signal.Monthly(),
        ti.Signal.VIX(high=30, low=20, data=vix_data),   # <-- pass here
        ti.Action.Rebalance(),
    ],
    ["low_vol_portfolio", "high_vol_portfolio"],
)
```

Each algo that accepts extra data documents its `data` parameter in its own reference page.