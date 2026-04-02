> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Setup

- [x] 1.1 Create `examples/notebooks/` directory
- [x] 1.2 Verify CSV test data files exist in `tests/data/` for QQQ, BIL, GLD, AAPL, ^VIX

## 2. Start of Month Rebalance Notebook

- [x] 2.1 Create `examples/notebooks/start_of_month_rebalance.ipynb` with title, description, and setup cells (imports, inline CSV_DATA, constants)
- [x] 2.2 Add data loading cell: `ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31", csv=CSV_DATA)`
- [x] 2.3 Add primary strategy: `Signal.Monthly()` + `Select.All()` + `Weigh.Ratio({"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1})` + `Action.Rebalance()`
- [x] 2.4 Add backtest run + `summary()` + `plot()` + `plot_security_weights()` + `plot_histogram()` + `trades.sample()`
- [x] 2.5 Add baselines: QQQ-only buy-and-hold (`Signal.Once()`), never-rebalanced same allocation (`Signal.Once()`)
- [x] 2.6 Add multi-backtest comparison: `ti.run(bt1, bt2, bt3)` → `summary()` + `plot()`

## 3. Volatility Targeting Notebook

- [x] 3.1 Create `examples/notebooks/volatility_targeting_qqq_bil_gld.ipynb` with title, description, and setup cells
- [x] 3.2 Add data loading and primary strategy: `Signal.Quarterly()` + `Weigh.BasedOnHV(initial_ratio, target_hv=0.15, lookback)`
- [x] 3.3 Add backtest run + results exploration (summary, plot, plot_security_weights, trades.sample)
- [x] 3.4 Add baselines: fixed 70/20/10 monthly + QQQ-only
- [x] 3.5 Add multi-backtest comparison
- [x] 3.6 Add target_hv sensitivity: re-run with `target_hv=0.10`, compare both

## 4. VIX Regime Switching Notebook

- [x] 4.1 Create `examples/notebooks/vix_target_rebalance.ipynb` with title, description, and setup cells
- [x] 4.2 Add VIX data loading: `ti.fetch_data(["^VIX"], csv=CSV_DATA)` + price data loading
- [x] 4.3 Add child portfolios: low_vol (QQQ 0.7/BIL 0.2/GLD 0.1) and high_vol (QQQ 0.4/BIL 0.4/GLD 0.2)
- [x] 4.4 Add parent portfolio: `Signal.Monthly()` + `Signal.VIX(high=30, low=20, data=vix_data)` + `Action.Rebalance()` with children
- [x] 4.5 Add backtest run + results exploration
- [x] 4.6 Add baselines + multi-backtest comparison

## 5. Dollar-Neutral Pair Trade Notebook

- [x] 5.1 Create `examples/notebooks/dollar_neutral_txn_kvue.ipynb` with title, description (note: requires network for live data)
- [x] 5.2 Add data loading: `ti.fetch_data(["TXN", "KVUE", "BIL"], start="2023-09-01", end="2024-12-31")` (live fetch)
- [x] 5.3 Add long child (TXN) with `Weigh.Equally()` and short child (KVUE) with `Weigh.Equally(short=True)`
- [x] 5.4 Add parent portfolio with `Weigh.Ratio()` for hedge ratio book sizing + `Signal.Monthly()`
- [x] 5.5 Add backtest run + results exploration
- [x] 5.6 Add baselines (long-only TXN, 50/50 TXN+BIL) + multi-backtest comparison

## 6. Beta-Neutral Dynamic Notebook

- [x] 6.1 Create `examples/notebooks/beta_neutral_dynamic.ipynb` with title, description, and setup cells
- [x] 6.2 Add data loading: QQQ/BIL/GLD prices + AAPL as beta reference base_data
- [x] 6.3 Add primary strategy: `Signal.Monthly()` + `Select.All()` + `Weigh.BasedOnBeta(initial_ratio, target_beta=0, lookback, base_data=aapl_data)` + `Action.Rebalance()`
- [x] 6.4 Add backtest run + results exploration (full_summary, plot_security_weights, trades.sample)
- [x] 6.5 Add baselines (equal-weight, QQQ-only) + multi-backtest comparison

## 7. Verification

- [x] 7.1 Run each notebook with `uv run jupyter execute` or equivalent to verify no errors
- [x] 7.2 Verify all notebooks produce expected output cells (charts, tables)
