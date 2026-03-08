## Context

The current Dollar Neutral strategy uses fixed 50/50 allocation (`RATIO = 1.0`) which successfully reduces portfolio beta for the V/MA pair but results in very low Sharpe Ratio. This occurs because fixed weights do not account for the different historical volatilities of the two assets. When one asset is significantly more volatile than the other, equal dollar allocation creates an imbalanced risk profile.

The existing `DollarNeutral` allocation strategy in `src/tiportfolio/allocation/dollar_neutral.py` uses a static ratio parameter, limiting its ability to adapt to changing market conditions and volatility regimes.

## Goals / Non-Goals

**Goals:**
- Implement a Dynamic Hedge Ratio for the Dollar Neutral strategy based on rolling volatility
- Replace fixed `RATIO = 1.0` with dynamic calculation using 60-day rolling standard deviation
- Improve the Sharpe Ratio of the V/MA pair by dynamically sizing positions based on relative volatility
- Maintain the dollar-neutral beta reduction benefit while optimizing risk-adjusted returns

**Non-Goals:**
- Modifying the core BacktestEngine or run_backtest functionality
- Breaking existing DollarNeutral strategy (this is additive functionality)
- Changing the fundamental portfolio optimization algorithm
- Implementing other risk management features beyond volatility-based sizing

## Decisions

**Dynamic Ratio Formula**
- Calculate rolling standard deviation for both LONG and SHORT assets over 60-day window
- Target Ratio = Volatility(Long) / Volatility(Short)
- If Long is twice as volatile as Short, allocate twice as much capital to Short position
- This ensures risk contribution from both positions is approximately equal

**Implementation Approach**
- Create new notebook `dollar_neutral_dynamic_v_ma.ipynb` for initial testing and validation
- Implement volatility calculation using pandas `.rolling().std()` method
- Pass dynamic weights to existing `ScheduleBasedEngine` without engine modifications
- Keep core engine unchanged - all logic handled at allocation/notebook level

**Volatility Window Selection**
- Use 60-day rolling window as starting point (approximately 3 trading months)
- Window length configurable for experimentation and optimization
- Ensure sufficient data points for reliable volatility estimation while maintaining responsiveness

## Risks / Trade-offs

**Increased Complexity** → More sophisticated allocation logic
- Risk: Additional parameters and calculations may make strategy harder to understand
- Mitigation: Clear documentation and visualization of dynamic ratio over time

**Computational Overhead** → Rolling calculations on each rebalance date
- Risk: Additional processing time for volatility calculations
- Mitigation: Negligible impact compared to data fetching and backtest simulation costs

**Overfitting Risk** → Dynamic parameters might be optimized for historical data
- Risk: 60-day window might not work well in all market regimes
- Mitigation: Test across different time periods and consider adaptive window selection
