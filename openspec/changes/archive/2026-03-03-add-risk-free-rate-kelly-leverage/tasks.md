## 1. Engine Modifications

- [x] 1.1 Add risk_free_rate parameter (default 0.04) to ScheduleBasedEngine.__init__
- [x] 1.2 Add risk_free_rate parameter (default 0.04) to VolatilityBasedEngine.__init__
- [x] 1.3 Store risk_free_rate as instance attribute in both engine classes
- [x] 1.4 Update run() methods to pass risk_free_rate to compute_metrics calls

## 2. Metrics Modifications

- [x] 2.1 Add kelly_leverage calculation to compute_metrics function using formula: annualized_mean_excess_return / (annualized_std_dev ** 2)
- [x] 2.2 Verify Sharpe ratio calculation is properly annualized (confirm current implementation)
- [x] 2.3 Update compute_metrics to include kelly_leverage in returned dictionary

## 3. Testing and Validation

- [x] 3.1 Test engine initialization with default risk_free_rate (0.04)
- [x] 3.2 Test engine initialization with custom risk_free_rate value
- [x] 3.3 Test compute_metrics returns kelly_leverage key
- [x] 3.4 Run VIX notebook to ensure no regressions and new features work
- [x] 3.5 Add Test cases to test computer metrics return correct result from sample data (tests/data/aapl.csv). Sharpe Ratio, CAGR, Kelly Leverage, MAR Ratio, Max Drawdown etc. 
- [x] 3.8 Update @[tests/data/qqq_bil_gld_2018_2024_summary.csv] and @[tests/test_simple_rebalance_qqq_bil_gld_rebalance.py] to match the changes
- [x] 3.10 Create test case using @[tests/data/aapl.csv] from 2018 to 2024 to test compute_metrics @[src/tiportfolio/metrics.py] returns accurate results and contains all attributes 
