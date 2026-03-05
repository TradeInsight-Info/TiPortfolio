## Why

Strategy comparison currently shows raw (unleveraged) metrics, making it impossible to evaluate how leverage and borrowing costs affect risk-adjusted performance. Traders who run leveraged portfolios need to compare strategies on their actual levered outcomes.

## What Changes

- Both `compare_strategies()` and `plot_strategy_comparison_interactive()` gain two new optional parameters: `leverages` and `yearly_loan_rates` (each a `float` or `list[float]`, default `1.0` / `0.0`)
- If a list is passed, it must match the length of `results` / `strategies` (and `names`); validation raises `ValueError` otherwise
- **`compare_strategies()`** — before building the comparison table, each strategy's metrics are adjusted for its leverage and loan rate:
  - `max_drawdown`: `L × original_max_drawdown`
  - `cagr`: `L × original_cagr − (L − 1) × yearly_loan_rate`
  - `mar_ratio`: `leveraged_cagr / leveraged_max_drawdown`
  - `sharpe_ratio`, `sortino_ratio`: **unchanged** (leverage scales both excess return and volatility equally)
- **`plot_strategy_comparison_interactive()`** — for each strategy with L ≠ 1.0, the equity curve is reconstructed from daily returns: `leveraged_r[t] = L × r[t] − (L−1) × yearly_loan_rate / 252`; the reconstructed curve is plotted in place of the raw curve
- When leverage ≠ 1 or loan rate ≠ 0, the strategy's name in column headers / chart legend is decorated: `"Name (L1.5x)"` or `"Name (L1.5x, r5.0%)"`

## Capabilities

### New Capabilities
- `leveraged-comparison`: Adjust strategy metrics for leverage and borrowing cost in `compare_strategies()`; reconstruct leveraged equity curves for `plot_strategy_comparison_interactive()`

### Modified Capabilities
- (none — existing spec requirements do not change; this extends the function signature)

## Impact

- `src/tiportfolio/report.py`: `compare_strategies()` and `plot_strategy_comparison_interactive()` signatures; new module-level helpers `_normalize_leverage_param`, `_build_display_name`, `_apply_leverage`, `_make_leveraged_equity_curve`
- `tests/test_report.py`: new tests for both leveraged table comparison and leveraged chart curve reconstruction
