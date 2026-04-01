## Context

`_SingleResult` in `result.py` currently computes 11 metrics in `summary()` and 15 in `full_summary()`. The metric order in `summary()` is arbitrary (risk_free_rate first), and `full_summary()` lacks the comprehensive statistics expected of a professional portfolio tearsheet. All computation is self-contained within `_SingleResult`, using the equity curve (`pd.Series`), `TiConfig`, and trade metadata.

## Goals / Non-Goals

**Goals:**
- Reorder `summary()` so the 5 most decision-relevant metrics appear first
- Round all float output to 3 decimal places for readability
- Expand `full_summary()` to ~55 metrics across 6 sections (existing + 4 new)
- Keep all computation in `_SingleResult` — no new classes or files

**Non-Goals:**
- Changing `BacktestResult` delegation logic (it already delegates to `_SingleResult`)
- Adding new dependencies (everything uses pandas/numpy/math already imported)
- Changing the equity curve format or `TiConfig` fields
- Benchmark comparisons (alpha, beta, information ratio) — future work

## Decisions

### 1. Rounding approach: round at the end, not per-computation

Round all values in the final dict before constructing the DataFrame, not during intermediate calculations. This preserves full precision in chained computations (e.g., Calmar depends on CAGR and MaxDD).

**Alternative considered**: Round each metric inline → rejected because intermediate rounding would compound errors in derived metrics.

Implementation: a helper `_round(val, n=3)` that skips non-float types (int for `rebalance_count`).

### 2. Period returns: use `searchsorted` for lookback date matching

For period returns (mtd, 3m, etc.), find the nearest equity curve date on or after the target lookback date using `equity.index.searchsorted()`. This handles weekends/holidays gracefully without requiring business-day calendar logic.

**Alternative considered**: `pd.DateOffset` subtraction + `asof()` → works but `searchsorted` on the DatetimeIndex is simpler and faster.

Return `float('nan')` for periods exceeding available data length (per spec).

### 3. Frequency resampling: use existing pandas patterns

Monthly: `equity.resample("ME").last().pct_change().dropna()` — already used in current `full_summary()`.
Yearly: `equity.resample("YE").last().pct_change().dropna()` — same pattern.

Sharpe/Sortino at each frequency use the same formula as `summary()` but with frequency-appropriate annualisation factors: monthly → `sqrt(12)`, yearly → `1.0`.

### 4. Drawdown episodes: identify via contiguous groups

Use `(equity < cummax)` boolean series, then group contiguous `True` runs to identify episodes. For each episode, record the trough depth and duration in days. This reuses the `cummax` already computed in `summary()`.

### 5. Extract helper methods to reduce full_summary() length

Factor out computation blocks into private methods on `_SingleResult`:
- `_period_returns() -> dict[str, float]`
- `_daily_stats() -> dict[str, float]`
- `_monthly_stats() -> dict[str, float]`
- `_yearly_stats() -> dict[str, float]`
- `_drawdown_analysis() -> dict[str, float]`

`full_summary()` becomes: call `summary()` base, then merge each section dict.

## Risks / Trade-offs

- **[Breaking change]** Metric order change in `summary()` → Tests asserting positional index will break. Mitigation: update tests in the same commit.
- **[NaN in output]** Period returns can be NaN for short backtests → Downstream code displaying the DataFrame must handle NaN. Mitigation: NaN is standard pandas convention; `round()` preserves NaN.
- **[Yearly stats unreliable with < 3 years]** Yearly Sharpe/Sortino with 1–2 data points are meaningless → Mitigation: return 0.0 when `len(yearly) < 2` (per spec).
- **[Performance]** Adding ~40 metrics increases `full_summary()` runtime → Mitigation: all operations are vectorised pandas/numpy on small Series (typically < 5000 bars). Negligible impact.
