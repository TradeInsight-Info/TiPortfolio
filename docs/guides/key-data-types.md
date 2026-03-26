## Key Data Types


### `TiConfig` — Global Defaults

```python
import tiportfolio as ti

config = ti.TiConfig(
    fee_per_share=0.0035,    # commission per share traded
    risk_free_rate=0.04,     # annualised, used for Sharpe/Sortino calculation
    initial_capital=10_000,  # starting portfolio value
    bars_per_year=252,       # trading days per year (adjust for intraday data)
    benchmark="SPY",         # optional; buy-and-hold comparison shown on plot()
)

result = ti.run(ti.Backtest(portfolio, data, config=config))
```

`bars_per_year` depends on your data frequency:

| Frequency | Value |
|---|---|
| Daily (default) | `252` |
| Hourly | `252 * 6.5 ≈ 1638` |
| Minute | `252 * 6.5 * 60 ≈ 98_280` |

You can also override `fee_per_share` directly on `Backtest` without creating a full config:

```python
ti.Backtest(portfolio, data, fee_per_share=0.005)
```


### `WeighFixedRatio` — Weight Normalisation

If weights do not sum to 1.0, the engine normalises them proportionally before execution:

```python
# These two are equivalent:
ti.algo.WeighFixedRatio(weights={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1})   # sums to 1.0
ti.algo.WeighFixedRatio(weights={"QQQ": 70, "BIL": 20, "GLD": 10})       # normalised to same

# Intentional cash buffer: weights summing to < 1.0 are respected as-is (no normalisation)
# Only over-weight cases (sum > 1.0) are normalised down.
```


### Price Data Format

`ti.fetch_data()` returns a DataFrame with a MultiIndex of `(date, symbol)` and OHLCV columns:

```
                       open    high     low   close    volume
date       symbol
2019-01-02 QQQ       153.20  154.10  152.80  153.75  30_000_000
           BIL        91.52   91.53   91.51   91.52     500_000
           GLD       120.10  120.50  119.80  120.20   5_000_000
...
```

Inside algo implementations, `context.prices` exposes the same format, sliced up to the current evaluation date.


### `context.selected` and `context.weights`

These fields are the communication channel between algo stages in a stack:

| Field | Type | Written by | Read by |
|---|---|---|---|
| `selected` | `list[str]` | Select algos | Weigh algos, Rebalance |
| `weights` | `dict[str, float]` | Weigh algos, WeighSelected | Rebalance |
| `selected_child` | `Portfolio \| None` | VixSignal (and other signal algos) | WeighSelected, engine |

In **parent portfolios** (children are `Portfolio` objects), `selected` contains child portfolio names rather than ticker strings. `WeighEqually()` and `WeighFixedRatio()` work the same way — operating on names rather than tickers.
