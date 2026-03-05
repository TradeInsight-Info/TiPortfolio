## Context

`allocation.py` currently has one concrete strategy: `FixRatio` (static weights). The `AllocationStrategy` protocol already supports arbitrary strategies through `get_symbols()` + `get_target_weights(..., **context)`, but the backtest loop never injects historical price data into `context`, so any strategy requiring rolling statistics (volatility, beta) has no data to work with.

Additionally, the backtest engine models portfolio state as `total_equity = sum(positions_dollars)`. This works for long-only portfolios where weights sum to 1.0, but breaks for dollar-neutral / beta-neutral strategies where weights could sum to ~0 and shorts produce negative dollar values.

## Goals / Non-Goals

**Goals:**
- Inject `prices_history` (prices up to current date) into `context` on every `get_target_weights()` call so any strategy can compute rolling statistics
- Implement `VolatilityTargeting` (long-only, inverse-vol weights)
- Implement `DollarNeutral` (long-short requiring a cash/safe-haven symbol for margin)
- Implement `BetaNeutral` (long-short, zero net beta, requiring a cash symbol)
- Keep the `AllocationStrategy` protocol unchanged (no signature change)
- Keep the weight-sum-to-1.0 invariant by requiring long-short strategies to include a `cash_symbol`

**Non-Goals:**
- Naked short selling without a collateral position — not financially sound and would break `total_equity` tracking
- Portfolio optimisation via external solvers (e.g., cvxpy) — `numpy` linalg suffices for the strategies here
- Changing `FixRatio` or existing VIX-regime strategies

## Decisions

**Historical data injection via context (not protocol change)**

Adding `prices_history` as an explicit protocol parameter would be a breaking change. Instead, `run_backtest()` passes it in `**context` on rebalance calls:

```python
context = {"prices_history": prices_df.loc[:date]}
weights = allocation.get_target_weights(date, equity, positions, row, **context)
```

Existing strategies receive and ignore `prices_history`. New strategies consume it. No protocol change needed.

**Long-short requires a `cash_symbol` — weights must still sum to 1.0**

The engine computes `total_equity = sum(positions_dollars)`. For this to equal NAV correctly, all capital must be represented as positions, including the collateral backing short trades. Both `DollarNeutral` and `BetaNeutral` require a `cash_symbol` (e.g., `"BIL"`, `"SHV"`) that absorbs residual cash. This keeps the sum-to-1.0 invariant and is financially realistic (short positions require margin collateral).

Example dollar-neutral weights: `{SPY: 0.5, AAPL: -0.5, BIL: 1.0}` → sum = 1.0 ✓

**Volatility Targeting: inverse-vol weighting, long-only**

```
realized_vol_i = std(daily_returns_i over lookback_days) × √252
raw_weight_i   = 1 / realized_vol_i
w_i            = raw_weight_i / Σ raw_weight_j   (normalized, sum to 1.0)
```

If `target_vol` is provided, apply a scaling step: `scalar = target_vol / portfolio_vol` where `portfolio_vol = √(wᵀΣw)` using the sample covariance of returns (diagonal approximation if preferred). Clamp scalar to `[0, max_leverage]` (default max 1.0 to keep long-only).

**Dollar Neutral: fixed intra-book ratios, tolerance-band rebalancing**

User provides:
- `long_weights: dict[str, float]` (within-book proportions, sum to 1.0)
- `short_weights: dict[str, float]` (within-book proportions, sum to 1.0)
- `cash_symbol: str`
- `book_size: float = 0.5` (fraction of equity in each book; default = 50% long + 50% short)
- `tolerance: float = 0.05` (max net imbalance as fraction of equity before rebalancing)

Target weights (when rebalancing):
- long symbol i: `book_size × long_weights[i]`
- short symbol j: `−book_size × short_weights[j]`
- cash: `1.0 − book_size × (sum_long − sum_short) = 1.0` (always 1.0 when long and short are balanced)

Tolerance-band gate in `get_target_weights()`:
```
long_value  = Σ positions_dollars[s] for s in long book
short_value = |Σ positions_dollars[s]| for s in short book
imbalance   = abs(long_value − short_value) / total_equity

if imbalance ≤ tolerance (and positions non-empty):
    return current weights  # no trades
else:
    return target weights   # rebalance
```

The initial allocation (`positions_dollars` empty) always returns target weights.

**Beta Neutral: OLS rolling beta, solve for zero-beta weights**

User provides `long_symbols`, `short_symbols`, `cash_symbol`, `benchmark_symbol="SPY"`, `benchmark_prices: pd.DataFrame | None`, `lookback_days`, `book_size`.

`get_symbols()` returns only `long_symbols + short_symbols + [cash_symbol]`. The `benchmark_symbol` is NOT in the traded universe and does NOT appear in returned weights.

Benchmark price data:
- If `benchmark_prices: pd.DataFrame` is provided at construction (OHLCV), use its close column directly (useful for tests and offline use).
- Otherwise, call `fetch_prices([benchmark_symbol], start, end)` inside `get_target_weights()` using the date range of `prices_history`. Cache the result on the instance (`_cached_benchmark`) to avoid redundant fetches per backtest.

Beta formula:
```
β_i = Cov(r_i, r_benchmark) / Var(r_benchmark)   [over lookback window]
```

Target: `Σ w_i × β_i = 0`, `Σ |w_i| = 2 × book_size` (gross exposure), `cash = 1.0 − net_exposure`.

For two symbols (one long L, one short S): solved analytically:
```
w_L = 2 × book_size × β_S / (β_S − β_L)
w_S = −(2 × book_size − w_L)
```
For N symbols: equal weights within each book (full optimisation is a non-goal).

If beta cannot be computed (insufficient history, missing benchmark), fall back to equal-weight within each book with a logged warning.

## Risks / Trade-offs

- [Risk] `prices_history` slice on every rebalance is O(n) memory per call → Mitigation: the slice is a view (pandas), not a copy; acceptable for typical backtests
- [Risk] Insufficient history on first N days for rolling vol/beta computation → Mitigation: fall back to equal weights when fewer than `lookback_days` rows available; log a warning via `helpers/log.py`
- [Risk] `prices_history` not passed in context if user calls `get_target_weights()` directly → Mitigation: strategies must handle `context.get("prices_history") is None` with an equal-weight fallback
- [Trade-off] Cash symbol required for long-short adds complexity for the user — accepted as financially realistic; without it, `total_equity` tracking breaks
- [Trade-off] Beta Neutral uses diagonal covariance (per-asset beta vs benchmark) not a full covariance matrix — simpler, deterministic, avoids matrix inversion instability
