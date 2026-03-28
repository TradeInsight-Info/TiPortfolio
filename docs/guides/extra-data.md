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

# Signal.VIX requires Portfolio objects as children, not strings.
# children[0] = low-vol regime, children[1] = high-vol regime.
low_vol = ti.Portfolio(
    'low_vol',
    [
        ti.Select.All(),
        ti.Weigh.Ratio(weights={"QQQ": 0.8, "BIL": 0.15, "GLD": 0.05}),
        ti.Action.Rebalance(),
    ],
    tickers,
)

high_vol = ti.Portfolio(
    'high_vol',
    [
        ti.Select.All(),
        ti.Weigh.Ratio(weights={"QQQ": 0.5, "BIL": 0.4, "GLD": 0.1}),
        ti.Action.Rebalance(),
    ],
    tickers,
)

portfolio = ti.Portfolio(
    'vix_regime',
    [
        ti.Signal.Monthly(),
        ti.Signal.VIX(high=30, low=20, data=vix_data),   # <-- pass here
        ti.Action.Rebalance(),
    ],
    [low_vol, high_vol],   # Portfolio objects, not strings
)
```

Each algo that accepts extra data documents its `data` parameter in its own reference page.


### Validating Alignment Before Running

Use `ti.validate_data()` to catch index mismatches before running a backtest:

```python
import tiportfolio as ti

tickers = ["QQQ", "BIL", "GLD"]
data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")
vix_data = ti.fetch_data(["^VIX"], start="2019-01-01", end="2024-12-31")

# check alignment explicitly before constructing Backtest
ti.validate_data(data, extra=vix_data)  # vix_data is already dict[str, pd.DataFrame]

portfolio = ti.Portfolio(
    'vix_regime',
    [
        ti.Signal.Monthly(),
        ti.Signal.VIX(high=30, low=20, data=vix_data),
        ti.Action.Rebalance(),
    ],
    [low_vol, high_vol],
)

result = ti.run(ti.Backtest(portfolio, data))
```

`ti.Backtest` also calls `validate_data` automatically at construction time, so you will always see a clear `ValueError` if indices are misaligned — even if you skip the explicit call above.