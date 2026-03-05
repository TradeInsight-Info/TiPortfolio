## 1. Update compare_strategies signature and validation

- [x] 1.1 Add `leverages: float | list[float] = 1.0` and `yearly_loan_rates: float | list[float] = 0.0` keyword parameters to `compare_strategies()`
- [x] 1.2 Add a `_normalize_leverage_param(value, n)` helper that converts a scalar to `[value] * n` or validates a list has length `n`; raise `ValueError` with a clear message on mismatch

## 2. Implement metric adjustment

- [x] 2.1 Add a `_apply_leverage(metrics, L, r)` function that returns a copy of the metrics dict with adjusted `max_drawdown`, `cagr`, and `mar_ratio` (recomputed from leveraged values); `sharpe_ratio` and `sortino_ratio` are passed through unchanged
- [x] 2.2 In `compare_strategies()`, call `_normalize_leverage_param` for both params, then apply `_apply_leverage` per strategy before building comparison rows

## 3. Column header decoration

- [x] 3.1 After normalising leverages/rates, build display names: if `L != 1.0` and `r == 0.0` → `"{name} (L{L}x)"`; if `L != 1.0` and `r != 0.0` → `"{name} (L{L}x, r{r:.1%})"` ; if `L == 1.0` → unchanged
- [x] 3.2 Use decorated names as DataFrame column headers (replacing bare `names`)

## 4. Tests — compare_strategies

- [x] 4.1 Test scalar leverage applied to all strategies: assert `max_drawdown`, `cagr`, `mar_ratio` adjusted correctly; assert `sharpe_ratio` and `sortino_ratio` unchanged
- [x] 4.2 Test per-strategy leverage list: one strategy at 1.0×, another at 1.5×; assert only the second strategy's metrics are adjusted
- [x] 4.3 Test `ValueError` raised when `leverages` list length != number of results
- [x] 4.4 Test `ValueError` raised when `yearly_loan_rates` list length != number of results
- [x] 4.5 Test column header decoration: leveraged column gets `(L1.5x)` suffix; un-leveraged column unchanged
- [x] 4.6 Test column header decoration with loan rate: `(L1.5x, r5.0%)` format
- [x] 4.7 Test default behaviour (leverage=1.0, rate=0.0) produces identical output to current behaviour and no column decoration

## 5. Update plot_strategy_comparison_interactive

- [x] 5.1 Add `leverages: float | list[float] = 1.0` and `yearly_loan_rates: float | list[float] = 0.0` keyword parameters to `plot_strategy_comparison_interactive()`; call `_normalize_leverage_param` for both
- [x] 5.2 Add `_make_leveraged_equity_curve(equity_curve, L, r)` helper: compute `pct_change()` daily returns, apply `L × r_t − (L−1) × rate/252`, reconstruct via `cumprod` starting from `equity_curve.iloc[0]`
- [x] 5.3 In the trace loop, replace `strategy.equity_curve` with the leveraged curve (or original if L=1.0 and r=0.0); use decorated display name from `_build_display_name` for both `name=` and `hovertemplate`

## 6. Tests — plot_strategy_comparison_interactive

- [x] 6.1 Test that with default params (L=1.0, r=0.0), the figure trace Y-values match the original equity curves and legend names are undecorated
- [x] 6.2 Test that with leverage L=1.5, the first Y-value of the leveraged trace equals `equity_curve.iloc[0]` (starting equity preserved) and subsequent values differ from raw
- [x] 6.3 Test that `ValueError` is raised when `leverages` list length != number of strategies
