## 1. Notebook Setup and Data Preparation

- [X] 1.1 Create `notebooks/dollar_neutral_dynamic_v_ma.ipynb` notebook
- [X] 1.2 Import required libraries (pandas, numpy, matplotlib, tiportfolio)
- [X] 1.3 Load historical price data for V (Long) and MA (Short) assets
- [X] 1.4 Set up backtest parameters (start date, end date, rebalance frequency)
- [X] 1.5 Create baseline fixed 50/50 ratio backtest for comparison

## 2. Dynamic Ratio Implementation

- [X] 2.1 Implement rolling volatility calculation function
  - [X] 2.1.1 Use 60-day rolling window with `.rolling(window=60).std()`
  - [X] 2.1.2 Calculate separate volatility series for Long and Short assets
  - [X] 2.1.3 Handle edge cases (insufficient data, NaN values)
- [X] 2.2 Implement dynamic hedge ratio formula
  - [X] 2.2.1 Calculate `Target Ratio = Volatility(Long) / Volatility(Short)`
  - [X] 2.2.2 Convert ratio to portfolio weights (normalize to sum to 1.0)
  - [X] 2.2.3 Add ratio bounds/clamping to prevent extreme allocations
- [X] 2.3 Create custom allocation logic for dynamic weights
  - [X] 2.3.1 Implement function to generate weights on each rebalance date
  - [X] 2.3.2 Integrate with existing `ScheduleBasedEngine` interface
  - [X] 2.3.3 Test weight calculation and validation

## 3. Backtesting and Analysis

- [X] 3.1 Run dynamic ratio backtest using `ScheduleBasedEngine`
- [X] 3.2 Calculate performance metrics (Sharpe, CAGR, Max Drawdown)
- [X] 3.3 Generate comparison plots
  - [X] 3.3.1 Equity curves: Fixed vs Dynamic ratio
  - [X] 3.3.2 Dynamic ratio time series visualization
  - [X] 3.3.3 Volatility comparison of both assets over time
- [X] 3.4 Analyze rebalance decisions and allocation changes
- [X] 3.5 Compare key metrics: Sharpe Ratio improvement, beta reduction effectiveness

## 4. Validation and Testing

- [X] 4.1 Validate dynamic ratio calculations against manual computations
- [X] 4.2 Test edge cases (market crashes, volatility spikes)
- [X] 4.3 Verify dollar-neutral properties are maintained (beta near zero)
- [X] 4.4 Test different volatility windows (30, 60, 90 days) for optimization
- [X] 4.5 Ensure backward compatibility with existing fixed ratio approach

## 5. Documentation and Code Organization

- [ ] 5.1 Document the dynamic ratio methodology and formulas
- [ ] 5.2 Add inline comments explaining volatility calculations
- [ ] 5.3 Create summary of findings and performance improvements
- [ ] 5.4 Evaluate if separate allocation strategy class is needed
  - [ ] 5.4.1 If yes, create `DollarNeutralDynamic` class in `src/tiportfolio/allocation/`
  - [ ] 5.4.2 If no, document notebook-based approach for future reference

## 6. Final Review and Integration

- [ ] 6.1 Review all calculations and ensure mathematical correctness
- [ ] 6.2 Verify plots are clear and effectively communicate results
- [ ] 6.3 Check that notebook runs end-to-end without errors
- [ ] 6.4 Prepare summary of Sharpe Ratio improvement and key insights
- [ ] 6.5 Document any limitations or areas for future enhancement
