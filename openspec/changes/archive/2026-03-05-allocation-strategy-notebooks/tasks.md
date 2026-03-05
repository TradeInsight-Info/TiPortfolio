## 1. DollarNeutral: asymmetric book sizing

- [x] 1.1 Add `long_book_size: float | None = None` and `short_book_size: float | None = None` fields to `DollarNeutral` dataclass in `allocation.py`
- [x] 1.2 Update `_target_weights()` to use `lbs = long_book_size if long_book_size is not None else book_size` (and same for `sbs`); apply `lbs` to long side and `sbs` to short side
- [x] 1.3 Add tests in `tests/test_allocation_dollar_neutral.py`: asymmetric sizes produce correct weights and correct TXN:KVUE = 1:1.135 ratio; sum still equals 1.0; omitting per-side sizes falls back to `book_size`
- [x] 1.4 Run `uv run pytest tests/test_allocation_dollar_neutral.py -q` and confirm all pass

## 2. BetaScreenerStrategy

- [x] 2.1 Create `src/tiportfolio/utils/beta_screener.py` with `BetaScreenerStrategy` dataclass: fields `universe`, `n_long`, `n_short`, `cash_symbol`, `benchmark_prices`, `lookback_days=60`, `book_size=0.5`; validate `cash_symbol not in universe` and `n_long + n_short <= len(universe)` in `__post_init__`
- [x] 2.2 Implement `get_symbols()` returning `universe + [cash_symbol]`
- [x] 2.3 Implement `_compute_betas(prices_history)`: extract last `lookback_days+1` rows, compute pct_change, align to benchmark close returns, return `dict[str, float]` of OLS beta per symbol; return `None` on insufficient data
- [x] 2.4 Implement `get_target_weights()`: call `_compute_betas`; if None, warn and return equal-weight fallback; else rank by beta, pick bottom-`n_long` as long book and top-`n_short` as short book; compute `short_book_size = book_size * avg_beta_long / avg_beta_short` (clamped 0.1–2.0); assign `+book_size/n_long` to longs, `-short_book_size/n_short` to shorts, zero to rest, cash absorbs net
- [x] 2.5 Export `BetaScreenerStrategy` from `src/tiportfolio/__init__.py`
- [x] 2.6 Write `tests/test_beta_screener.py`: construction validation, `get_symbols()` excludes benchmark, beta-neutral portfolio beta ≈ 0 with synthetic data, fallback on missing history, public import
- [x] 2.7 Run `uv run pytest tests/test_beta_screener.py -q` and confirm all pass

## 3. DollarNeutral notebook

- [x] 3.1 Create `notebooks/dollar_neutral_txn_kvue.ipynb` with cells: setup (imports, cache, constants with `RATIO=1.135`), data fetch (TXN, KVUE, BIL via YFinance), strategy construction (`long_book_size=1/(1+RATIO)`, `short_book_size=RATIO/(1+RATIO)`, `Schedule("month_mid")`), backtest + `result.summary()`
- [x] 3.2 Add chart cell: `plot_portfolio_with_assets_interactive(result, mark_rebalances=True)`
- [x] 3.3 Add rebalance table cell: `rebalance_decisions_table(result)`
- [x] 3.4 Add comparison cells: long-TXN-only, short-KVUE-only (negative-weight FixRatio or direct), fixed 50/50 TXN+BIL; `compare_strategies` + `plot_strategy_comparison_interactive`
- [x] 3.5 Add interpretation markdown cell explaining hedge ratio and spread P&L intuition
- [x] 3.6 Verify notebook executes: `uv run jupyter nbconvert --to notebook --execute notebooks/dollar_neutral_txn_kvue.ipynb --output /tmp/dn_test.ipynb`

## 4. VolatilityTargeting notebook

- [x] 4.1 Create `notebooks/volatility_targeting_qqq_bil_gld.ipynb` with cells: setup (imports, cache, `SYMBOLS=["QQQ","BIL","GLD"]`, `LOOKBACK=60`, `TARGET_VOL=None`), data fetch, strategy construction (`VolatilityTargeting`, `Schedule("month_mid")`), backtest + `result.summary()`
- [x] 4.2 Add chart cell: `plot_portfolio_with_assets_interactive(result, mark_rebalances=True)`
- [x] 4.3 Add weight evolution cell: extract per-rebalance weights from `result.rebalance_decisions`, plot as line chart showing QQQ/BIL/GLD weights over time
- [x] 4.4 Add rebalance table cell: `rebalance_decisions_table(result)`
- [x] 4.5 Add comparison cells: fixed 70/20/10 (FixRatio), long QQQ only; `compare_strategies` + `plot_strategy_comparison_interactive`
- [x] 4.6 Add target_vol demo cell: re-run with `TARGET_VOL=0.10`, compare to uncapped version showing de-levering effect
- [x] 4.7 Add interpretation markdown cell explaining inverse-vol weighting and target_vol mechanics
- [x] 4.8 Verify notebook executes: `uv run jupyter nbconvert --to notebook --execute notebooks/volatility_targeting_qqq_bil_gld.ipynb --output /tmp/vt_test.ipynb`

## 5. BetaNeutral dynamic notebook

- [x] 5.1 Create `notebooks/beta_neutral_dynamic.ipynb` with cells: setup (imports, cache, `UNIVERSE` list of 20 stocks, `CASH="BIL"`, `BENCHMARK="SPY"`, `N_LONG=5`, `N_SHORT=5`, `LOOKBACK=60`, `START`, `END`)
- [x] 5.2 Add data fetch cell: fetch all 21 symbols (universe + BIL) + SPY via YFinance; show shape; build `spy_df` DataFrame for `benchmark_prices`
- [x] 5.3 Add strategy construction cell: `BetaScreenerStrategy(universe=UNIVERSE, n_long=N_LONG, n_short=N_SHORT, cash_symbol=CASH, benchmark_prices=spy_df, lookback_days=LOOKBACK)`; wrap in `ScheduleBasedEngine` with `Schedule("month_mid")`; pass all 21 symbols to `prices_df`
- [x] 5.4 Add backtest + `result.summary()` cell
- [x] 5.5 Add portfolio chart cell: `plot_portfolio_with_assets_interactive(result, mark_rebalances=True)`
- [x] 5.6 Add rolling book composition cell: extract from `rebalance_decisions.target_weights`, build a DataFrame of long/short book membership per date, display as table
- [x] 5.7 Add comparison cells: long SPY only, equal-weight universe; `compare_strategies` + `plot_strategy_comparison_interactive`
- [x] 5.8 Add disclaimer markdown cell: short selling requires margin account
- [x] 5.9 Verify notebook executes: `uv run jupyter nbconvert --to notebook --execute notebooks/beta_neutral_dynamic.ipynb --output /tmp/bn_test.ipynb`

## 6. Final verification

- [x] 6.1 Run `uv run pytest -q` and confirm all existing tests still pass (no regressions from DollarNeutral changes)
- [x] 6.2 Run `uv run mypy src/tiportfolio/allocation.py src/tiportfolio/utils/beta_screener.py src/tiportfolio/__init__.py` and resolve any type errors in new code
