## 1. Notebook Prototype Setup (KO/PEP)

- [X] 1.1 Create `notebooks/cointegration_pairs_ko_pep.ipynb` notebook
- [X] 1.2 Import required libraries (pandas, numpy, matplotlib, statsmodels, tiportfolio)
- [X] 1.3 Load historical price data for KO and PEP (2018-2024)
- [X] 1.4 Transform prices to log space: `log_price = ln(price)`
- [X] 1.5 Set up baseline parameters and visualization of price series

## 2. Johansen Cointegration Implementation

- [X] 2.1 Implement cointegration testing function
  - [X] 2.1.1 Use `statsmodels.tsa.vector_ar.vecm.coint_johansen`
  - [X] 2.1.2 Set appropriate det_order and k_ar_diff parameters
  - [X] 2.1.3 Handle test results and extract eigenvectors
- [x] 2.2 Calculate hedge ratio from eigenvectors
  - [x] 2.2.1 Extract first eigenvector: `hedge_ratio = eigenvector[0] / eigenvector[1]`
  - [x] 2.2.2 Validate hedge ratio reasonableness (e.g., 0.5-2.0 range)
  - [x] 2.2.3 Document mathematical derivation
- [x] 2.3 Calculate and analyze spread
  - [x] 2.3.1 Spread formula: `spread = log_price_KO - hedge_ratio * log_price_PEP`
  - [x] 2.3.2 Test spread stationarity using ADF test
  - [x] 2.3.3 Visualize spread time series and distribution

## 3. Z-Score Signal Generation

- [X] 3.1 Implement rolling Z-score calculation
  - [X] 3.1.1 Calculate rolling mean and std of spread (default 252-day window)
  - [X] 3.1.2 Z-score formula: `(spread - rolling_mean) / rolling_std`
  - [X] 3.1.3 Handle edge cases (insufficient data, NaN values)
- [X] 3.2 Implement signal logic
  - [X] 3.2.1 Entry signals: `z_score > 2.0` (short spread) or `z_score < -2.0` (long spread)
  - [X] 3.2.2 Exit signals: `z_score crosses 0` (mean reversion)
  - [X] 3.2.3 Position sizing: fixed allocation or volatility-based
- [ ] 3.3 Visualize signals and performance
  - [ ] 3.3.1 Plot Z-score time series with threshold lines
  - [ ] 3.3.2 Mark entry/exit points on price charts
  - [ ] 3.3.3 Calculate signal statistics (win rate, avg hold period)

## 4. Backtesting Architecture Evaluation

- [ ] 4.1 Test with existing ScheduleBasedEngine
  - [ ] 4.1.1 Create custom allocation strategy with signal logic
  - [ ] 4.1.2 Evaluate if schedule-based approach works for signal trading
  - [ ] 4.1.3 Identify limitations and requirements for event-driven approach
- [ ] 4.2 Design SignalBasedEngine (if needed)
  - [ ] 4.2.1 Define signal-driven backtesting interface
  - [ ] 4.2.2 Implement event-driven simulation loop
  - [ ] 4.2.3 Integrate with existing infrastructure
- [ ] 4.3 Performance comparison
  - [ ] 4.3.1 Compare cointegration vs volatility-based approaches
  - [ ] 4.3.2 Calculate Sharpe Ratio, CAGR, Max Drawdown
  - [ ] 4.3.3 Validate target Sharpe Ratio of 1.0 (2018-2024)

## 5. Validation and Testing

- [ ] 5.1 Validate cointegration calculations
  - [ ] 5.1.1 Cross-check hedge ratios with manual calculations
  - [ ] 5.1.2 Test different Johansen parameters
  - [ ] 5.1.3 Verify cointegration test statistical significance
- [ ] 5.2 Test signal robustness
  - [ ] 5.2.1 Different Z-score thresholds (1.5, 2.0, 2.5)
  - [ ] 5.2.2 Different rolling windows (126, 252, 504 days)
  - [ ] 5.2.3 Out-of-sample testing on different time periods
- [ ] 5.3 Risk management testing
  - [ ] 5.3.1 Maximum drawdown analysis
  - [ ] 5.3.2 Position sizing impact on performance
  - [ ] 5.3.3 Correlation with market factors

## 6. Documentation and Code Organization

- [ ] 6.1 Document methodology and mathematical foundations
- [ ] 6.2 Create reusable cointegration analysis functions
- [ ] 6.3 Evaluate if separate allocation strategy class is needed
  - [ ] 6.3.1 If yes, create `CointegrationPairs` class in `src/tiportfolio/allocation/`
  - [ ] 6.3.2 If new engine needed, implement in `src/tiportfolio/`
- [ ] 6.4 Add comprehensive comments and examples
- [ ] 6.5 Create summary of findings and performance metrics

## 7. Dynamic Pair Screening (Future Enhancement)

- [ ] 7.1 Design pair screening methodology
- [ ] 7.2 Implement batch cointegration testing
- [ ] 7.3 Create pair selection criteria
- [ ] 7.4 Test multiple pairs simultaneously
