> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Reorder summary() and add rounding

- [x] 1.1 Reorder the `data` dict in `_SingleResult.summary()` so the first 5 keys are `sharpe`, `calmar`, `sortino`, `max_drawdown`, `cagr`, followed by `risk_free_rate`, `total_return`, `kelly`, `final_value`, `total_fee`, `rebalance_count`
- [x] 1.2 Add a `_round_values(data: dict) -> dict` helper that rounds all float values to 3 decimal places, skipping int types
- [x] 1.3 Apply `_round_values()` at the end of `summary()` before constructing the DataFrame
- [x] 1.4 Update `tests/test_result.py::test_summary_has_key_metrics` to assert the top-5 index order and verify 3-decimal rounding

## 2. Extract helper methods for full_summary() sections

- [x] 2.1 Create `_period_returns(self) -> dict[str, float]` — compute mtd, 3m, 6m, ytd, 1y, 3y_ann, 5y_ann, 10y_ann, incep_ann from the equity curve. Use `searchsorted` for lookback date matching. Return NaN for periods exceeding data length.
- [x] 2.2 Create `_daily_stats(self) -> dict[str, float]` — compute daily_mean_ann, daily_vol_ann, daily_skew, daily_kurt, best_day, worst_day from daily returns
- [x] 2.3 Create `_monthly_stats(self) -> dict[str, float]` — compute monthly_sharpe, monthly_sortino, monthly_mean_ann, monthly_vol_ann, monthly_skew, monthly_kurt, best_month, worst_month from monthly returns
- [x] 2.4 Create `_yearly_stats(self) -> dict[str, float]` — compute yearly_sharpe, yearly_sortino, yearly_mean, yearly_vol, yearly_skew, yearly_kurt, best_year, worst_year from yearly returns
- [x] 2.5 Create `_drawdown_analysis(self) -> dict[str, float]` — compute avg_drawdown, avg_drawdown_days, avg_up_month, avg_down_month, win_year_pct, win_12m_pct

## 3. Update full_summary() to use helpers

- [x] 3.1 Refactor `full_summary()` to call `summary()` then merge results from `_period_returns()`, `_daily_stats()`, `_monthly_stats()`, `_yearly_stats()`, `_drawdown_analysis()`
- [x] 3.2 Apply `_round_values()` to the merged dict before constructing the DataFrame
- [x] 3.3 Remove the old inline max_dd_duration / best_month / worst_month / win_rate code (these are now covered by the helpers)

## 4. Update tests

- [x] 4.1 Add `test_period_return_keys_present` — verify all 9 period return keys exist in full_summary()
- [x] 4.2 Add `test_period_returns_nan_for_short_data` — verify 3y/5y/10y are NaN for 1-year backtest
- [x] 4.3 Add `test_daily_stats_keys_present` — verify all 6 daily stat keys exist
- [x] 4.4 Add `test_monthly_stats_keys_present` — verify all 8 monthly stat keys exist
- [x] 4.5 Add `test_yearly_stats_keys_present` — verify all 8 yearly stat keys exist
- [x] 4.6 Add `test_drawdown_analysis_keys_present` — verify all 6 drawdown keys exist
- [x] 4.7 Add `test_full_summary_rounding` — verify all float values have at most 3 decimal places
- [x] 4.8 Add `test_avg_drawdown_monotonic_equity` — verify avg_drawdown is 0.0 for always-increasing equity
- [x] 4.9 Add `test_win_rate_metrics_bounds` — verify win_year_pct and win_12m_pct are between 0.0 and 1.0
- [x] 4.10 Run full test suite: `uv run python -m pytest` — all tests pass
