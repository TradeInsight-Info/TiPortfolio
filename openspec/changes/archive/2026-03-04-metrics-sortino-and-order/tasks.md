## 1. Update metrics.py

- [x] 1.1 Add `mean_excess_return` calculation: `float(excess.mean() * periods_per_year)` using the existing `excess` series
- [x] 1.2 Add `sortino_ratio` calculation: annualised mean excess return divided by annualised downside std (std of `excess[excess < 0]`); return `nan` when downside std is 0 or no downside returns
- [x] 1.3 Reorder the return dict to: `sharpe_ratio`, `sortino_ratio`, `mar_ratio`, `cagr`, `max_drawdown`, `kelly_leverage`, `mean_excess_return`
- [x] 1.4 Update `_NAN_METRICS` dict to include `sortino_ratio` and `mean_excess_return` with `nan`, in the same canonical order

## 2. Update backtest.py summary

- [x] 2.1 Add "Sortino Ratio" and "Mean Excess Return" lines to `BacktestResult.summary()`, inserted after "Sharpe Ratio" in the canonical order

## 3. Update report.py comparison

- [x] 3.1 Replace `_COMPARE_METRICS` tuple with `("sharpe_ratio", "sortino_ratio", "mar_ratio", "cagr", "max_drawdown")`
- [x] 3.2 Add `sortino_ratio` to the higher-is-better set in the `compare_strategies()` best-value logic
- [x] 3.3 Remove `final_value` and `total_fee` special-case branches that are no longer in `_COMPARE_METRICS`

## 4. Update tests

- [x] 4.1 Update `tests/test_metrics.py`: assert `sortino_ratio` and `mean_excess_return` are present and finite for valid series; assert `nan` for empty/degenerate series; assert canonical key order
- [x] 4.2 Update `tests/test_report.py`: assert `compare_strategies` returns exactly 5 rows with correct index; assert `sortino_ratio` row identifies the correct better strategy
- [x] 4.3 Update any snapshot/string assertions in `tests/test_engine.py` or integration tests that check `result.summary()` output
- [x] 4.4 Replace range assertions for new metrics in `test_metrics_aapl_data` (L103-104) with exact `pytest.approx` values: `sortino_ratio ≈ 2.2062826094371797`, `mean_excess_return ≈ 0.6554567652180477` (both `rel=1e-9`)
