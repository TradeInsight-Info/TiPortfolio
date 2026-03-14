## Why

The current volatility-based dynamic weighting approach relies on empirical volatility ratios which may not capture the true long-term equilibrium relationship between paired assets. By shifting to a Cointegration-based Pairs Trading strategy, we can identify statistically robust mean-reverting relationships and calculate precise hedge ratios using the Johansen test. This mathematical approach should provide more reliable spread trading signals and potentially achieve the target Sharpe Ratio of 1.0 between 2018-2024.

Cointegration analysis directly addresses the core requirement of pairs trading: finding assets that move together in the long run but may diverge in the short term, creating profitable mean-reversion opportunities. The Johansen test provides both the hedge ratio (eigenvector) and statistical significance of the cointegrating relationship.

## What Changes

- **NEW**: Implement cointegration-based pairs trading using `statsmodels.tsa.vector_ar.vecm.coint_johansen`
- **NEW**: Calculate precise hedge ratios from eigenvectors instead of empirical volatility ratios
- **NEW**: Use log prices for cointegration calculation (more mathematically sound)
- **NEW**: Implement Z-score based signal logic with configurable thresholds (±2.0)
- **NEW**: Create event-driven/signal-based backtesting approach (evaluated against current ScheduleBasedEngine)
- **NEW**: Start with KO/PEP prototype notebook for validation
- **NEW**: Dynamic pair screening capability (after prototype validation)

**Key Implementation Details:**
- Use Johansen test to calculate eigenvectors representing hedge ratios (e.g., 1.135)
- Calculate spread = log_price_A - hedge_ratio * log_price_B
- Generate Z-score of spread: (spread - mean) / std_dev
- Trigger trades when Z-score > 2.0 (short spread) or < -2.0 (long spread)
- Exit positions when Z-score reverts to mean (0)

## Capabilities

### New Capabilities
- `cointegration-analysis`: Johansen test for hedge ratio calculation
- `z-score-signals`: Mean-reversion trading signals based on statistical thresholds
- `log-price-calculation`: Mathematically sound price transformation
- `event-driven-backtesting`: Signal-based trading (potentially new engine type)

### Enhanced Capabilities
- `pairs-trading`: More robust statistical foundation
- `market-neutral-strategies`: Improved hedge ratio precision

## Impact

- **Code**: New notebook `notebooks/cointegration_pairs_ko_pep.ipynb`
- **Code**: Potential new engine type for event-driven backtesting
- **Code**: New allocation strategy for cointegration-based pairs trading
- **Analysis**: Statistical validation of cointegration relationships
- **Performance**: Target Sharpe Ratio of 1.0 (2018-2024)
- **Compatibility**: May require new engine architecture evaluation
