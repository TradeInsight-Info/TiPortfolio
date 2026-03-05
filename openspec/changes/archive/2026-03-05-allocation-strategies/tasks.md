## 1. Engine: inject prices_history in context

- [x] 1.1 Write test in `tests/test_backtest.py`: spy that `get_target_weights` receives `prices_history` kwarg on rebalance dates (use a mock/spy strategy that captures context kwargs)
- [x] 1.2 Update `run_backtest()` in `backtest.py`: on each rebalance call, pass `prices_history=prices_df.loc[:date]` in the context dict
- [x] 1.3 Run existing tests to confirm `FixRatio` and `VixRegimeAllocation` are unaffected

## 2. VolatilityTargeting strategy

- [x] 2.1 Write tests in `tests/test_allocation_vol_targeting.py`:
  - construction: `get_symbols()` returns correct list
  - inverse-vol weights: higher-vol asset gets lower weight; weights sum to 1.0
  - target_vol scaling: when portfolio_vol > target_vol, scalar < 1.0; when ≤, weights unchanged
  - fallback (None): equal weights when `prices_history` not in context
  - fallback (insufficient rows): equal weights when fewer than `lookback_days + 1` rows
  - public import: `from tiportfolio import VolatilityTargeting`
- [x] 2.2 Implement `VolatilityTargeting` dataclass in `allocation.py`:
  - params: `symbols`, `lookback_days`, `target_vol=None`
  - inverse-vol formula, normalize, optional target_vol scalar clamped to `[0, 1.0]`
  - equal-weight fallback with `log.warning` when history missing or insufficient
- [x] 2.3 Export `VolatilityTargeting` from `src/tiportfolio/__init__.py`

## 3. DollarNeutral strategy

- [x] 3.1 Write tests in `tests/test_allocation_dollar_neutral.py`:
  - construction: `get_symbols()` includes long + short + cash symbols
  - construction raises `ValueError` when `long_weights` don't sum to 1.0
  - construction raises `ValueError` when `short_weights` don't sum to 1.0
  - construction raises `ValueError` when `cash_symbol` overlaps with long/short
  - within-tolerance: returns current weights (no trades) when `|long$ - short$| / equity <= tolerance`
  - outside-tolerance: returns target balanced weights when imbalance exceeds tolerance
  - empty positions_dollars: returns target weights for initial allocation
  - target weights sum to 1.0 and short symbols are negative
  - cash weight equals 1.0 for balanced default book_size=0.5
  - public import: `from tiportfolio import DollarNeutral`
- [x] 3.2 Implement `DollarNeutral` dataclass in `allocation.py`:
  - params: `long_weights`, `short_weights`, `cash_symbol`, `book_size=0.5`, `tolerance=0.05`
  - validate sums and no overlap in `__post_init__`
  - tolerance check: compute `abs(long_value - short_value) / total_equity`; return current weights if ≤ tolerance and positions non-empty; return target weights otherwise
  - target weights: `+book_size * lw[i]`, `-book_size * sw[j]`, cash = `1.0 - net`
- [x] 3.3 Export `DollarNeutral` from `src/tiportfolio/__init__.py`

## 4. BetaNeutral strategy

- [x] 4.1 Write tests in `tests/test_allocation_beta_neutral.py`:
  - construction: `get_symbols()` returns only long + short + cash (no benchmark)
  - construction raises `ValueError` on symbol overlap
  - pre-loaded `benchmark_prices` (OHLCV DataFrame) bypasses internal fetch
  - two-symbol beta-neutral: `sum(w_i * beta_i) ≈ 0` with sufficient history
  - weights sum to 1.0 with sufficient history
  - benchmark_symbol NOT in returned weights dict
  - fallback on `None` prices_history: equal weights within each book, sum to 1.0
  - fallback on insufficient history rows
  - fallback when benchmark prices unavailable (fetch raises)
  - public import: `from tiportfolio import BetaNeutral`
- [x] 4.2 Implement `BetaNeutral` dataclass in `allocation.py`:
  - params: `long_symbols`, `short_symbols`, `cash_symbol`, `benchmark_symbol="SPY"`, `benchmark_prices: pd.DataFrame | None = None`, `lookback_days=60`, `book_size=0.5`
  - `get_symbols()` returns only long + short + cash (no benchmark)
  - benchmark prices: use `benchmark_prices` if provided, else call `fetch_prices([benchmark_symbol], ...)` from date range of `prices_history`; cache result on instance
  - OLS beta: `Cov(r_i, r_benchmark) / Var(r_benchmark)` over lookback window
  - two-symbol analytic solve for zero net beta; N-symbol: equal-weight within each book
  - cash weight = `1.0 - net_exposure`; equal-weight fallback with `log.warning` on insufficient data or fetch error
- [x] 4.3 Export `BetaNeutral` from `src/tiportfolio/__init__.py`

## 5. Final verification

- [x] 5.1 Run full test suite (`uv run pytest`) and confirm all tests pass
- [x] 5.2 Run `uv run mypy src/` and resolve any type errors in new code
