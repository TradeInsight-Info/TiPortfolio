## 1. Update plot_portfolio_beta

- [x] 1.1 Add benchmark_symbol parameter (default "SPY")
- [x] 1.2 Add benchmark_prices parameter (default None)
- [x] 1.3 Auto-fetch from YFinance if benchmark_prices is None

## 2. Clean up report.py

- [x] 2.1 Remove deprecated plot_portfolio_with_assets_interactive function
- [x] 2.2 Keep essential functions (compare_strategies, rebalance_decisions_table, etc.)

## 3. Update notebooks with beta charts

- [x] 3.1 Update beta_neutral_dynamic.ipynb - already has custom beta
- [x] 3.2 Update dollar_neutral_txn_kvue.ipynb - added beta chart
- [x] 3.3 Update volatility_targeting_qqq_bil_gld.ipynb - added beta chart
- [x] 3.4 Update start_of_month_rebalance.ipynb - added beta chart
- [x] 3.5 Update vix_target_rebalance.ipynb - added beta chart
