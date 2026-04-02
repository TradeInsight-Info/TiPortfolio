# Demo Notebooks for Simplified TiPortfolio API

**Goal**: Create 5 Jupyter notebooks in `examples/notebooks/` that mirror the master-branch notebooks but use the new simplified `tiportfolio` API (Portfolio + Algo Stack pattern).
**Architecture**: Each notebook follows the same Signal → Select → Weigh → Action algo stack pattern, using `ti.Portfolio`, `ti.Backtest`, and `ti.run()`.
**Tech Stack**: Python 3.12, tiportfolio, pandas, matplotlib, plotly (optional for interactive)
**Spec**: openspec/changes/demo-notebooks-simplify/specs/

## File Map:

1. Create : `examples/notebooks/start_of_month_rebalance.ipynb` — Simplest: fixed ratio monthly rebalance (introductory notebook)
2. Create : `examples/notebooks/volatility_targeting_qqq_bil_gld.ipynb` — Inverse-vol weighted portfolio with BasedOnHV
3. Create : `examples/notebooks/vix_target_rebalance.ipynb` — VIX regime switching with Signal.VIX + parent/child tree
4. Create : `examples/notebooks/dollar_neutral_txn_kvue.ipynb` — Dollar-neutral pair trade using parent/child long/short tree
5. Create : `examples/notebooks/beta_neutral_dynamic.ipynb` — Beta-neutral dynamic strategy using Weigh.BasedOnBeta

## Chunks

### Chunk 1: Foundation notebook (start_of_month_rebalance)
The simplest strategy: fixed 70/20/10 QQQ/BIL/GLD with monthly rebalance. Serves as the intro to the new API. Compares: rebalanced vs buy-and-hold vs QQQ-only.

Files:
- `examples/notebooks/start_of_month_rebalance.ipynb`
Steps:
- Step 1: Fetch data with `ti.fetch_data()` using CSV for offline mode
- Step 2: Build portfolio with `Signal.Monthly()`, `Select.All()`, `Weigh.Ratio()`, `Action.Rebalance()`
- Step 3: Run backtest, show summary, plot equity curve
- Step 4: Create baselines (QQQ-only, never-rebalance) and compare with `ti.run(bt1, bt2, bt3)`
- Step 5: Show full_summary, trades.sample, plot_security_weights, plot_histogram

### Chunk 2: Volatility targeting notebook
Adaptive weights via inverse-vol targeting. Demonstrates `Weigh.BasedOnHV`.

Files:
- `examples/notebooks/volatility_targeting_qqq_bil_gld.ipynb`
Steps:
- Step 1: Fetch data, define initial ratio and target_hv
- Step 2: Build portfolio with `Weigh.BasedOnHV(initial_ratio, target_hv, lookback)`
- Step 3: Run with quarterly schedule, show weight evolution via `plot_security_weights()`
- Step 4: Compare against fixed-ratio and QQQ-only baselines
- Step 5: Re-run with different `target_hv` values to show sensitivity

### Chunk 3: VIX regime switching notebook
Regime-switching strategy that toggles between risk-on and risk-off allocations based on VIX levels.

Files:
- `examples/notebooks/vix_target_rebalance.ipynb`
Steps:
- Step 1: Load VIX data from CSV, fetch price data
- Step 2: Build two child portfolios (low_vol, high_vol) with different Weigh.Ratio
- Step 3: Build parent with `Signal.VIX(high, low, data)` to switch between children
- Step 4: Compare against QQQ-only and fixed-ratio baselines
- Step 5: Show regime transitions in chart

### Chunk 4: Dollar-neutral pair trade notebook
Long/short pair trade demonstrating parent/child portfolio tree.

Files:
- `examples/notebooks/dollar_neutral_txn_kvue.ipynb`
Steps:
- Step 1: Fetch TXN, KVUE, BIL data (live — KVUE since Sept 2023)
- Step 2: Build long child (TXN) and short child (KVUE) with Weigh.Equally(short=True)
- Step 3: Build parent with Weigh.Ratio to control book sizes (hedge ratio)
- Step 4: Compare against long-only TXN and 50/50 baselines
- Step 5: Show security weights and trade log

### Chunk 5: Beta-neutral dynamic notebook
Most complex: beta-neutral strategy using Weigh.BasedOnBeta with a broader universe.

Files:
- `examples/notebooks/beta_neutral_dynamic.ipynb`
Steps:
- Step 1: Define universe, fetch data including benchmark (AAPL as base)
- Step 2: Build portfolio with `Weigh.BasedOnBeta(initial_ratio, target_beta=0, lookback, base_data)`
- Step 3: Run backtest, show how weights adapt to maintain zero beta
- Step 4: Compare against equal-weight and QQQ-only baselines
- Step 5: Show weight evolution and summary metrics
