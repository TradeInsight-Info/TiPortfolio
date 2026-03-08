## Why

The current Dollar Neutral strategy using fixed 50/50 allocation (`RATIO = 1.0`) successfully reduces portfolio beta for the V/MA pair but achieves very low Sharpe Ratio. Analysis shows that the fixed ratio does not account for the significant difference in historical volatilities between V (Long) and MA (Short) assets. When one asset is more volatile than the other, equal dollar allocation creates an imbalanced risk contribution, leading to suboptimal risk-adjusted returns.

A dynamic hedge ratio based on rolling volatility would equalize the risk contribution from both positions, potentially improving the Sharpe Ratio while maintaining the beta reduction benefits of dollar-neutral positioning.

## What Changes

- **NEW**: Create `dollar_neutral_dynamic_v_ma.ipynb` notebook for testing and validation
- **NEW**: Implement dynamic hedge ratio calculation using 60-day rolling standard deviation
- **NEW**: Add volatility-based ratio formula: `Target Ratio = Volatility(Long) / Volatility(Short)`
- **NEW**: Generate comparison plots showing fixed vs dynamic ratio performance
- **NEW**: Optionally create a new `DollarNeutralDynamic` allocation strategy class if notebook approach proves successful

**Key Implementation Details:**
- Use pandas `.rolling(window=60).std()` for volatility calculation
- Calculate dynamic ratio on each rebalance date based on trailing volatility
- Pass calculated weights to existing `ScheduleBasedEngine` without engine modifications
- Maintain backward compatibility with existing fixed-ratio DollarNeutral strategy

## Capabilities

### New Capabilities
- `dynamic-hedge-ratio`: Volatility-based position sizing for dollar-neutral strategies
- `rolling-volatility-calculation`: 60-day rolling standard deviation for ratio determination
- `risk-balanced-allocation`: Equal risk contribution from long and short positions

### Enhanced Capabilities
- `dollar-neutral-strategy`: Improved Sharpe Ratio through dynamic sizing

## Impact

- **Code**: New notebook `notebooks/dollar_neutral_dynamic_v_ma.ipynb`
- **Code**: Optional new allocation class `src/tiportfolio/allocation/dollar_neutral_dynamic.py`
- **Analysis**: Performance comparison plots and metrics for fixed vs dynamic approaches
- **Compatibility**: No breaking changes - existing DollarNeutral strategy remains unchanged
- **Testing**: Validation against historical V/MA data to verify Sharpe Ratio improvement
