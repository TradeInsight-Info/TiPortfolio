## Why

To enhance the portfolio backtesting library with more accurate risk-adjusted performance metrics, we need to incorporate risk-free rate assumptions and provide Kelly leverage calculations for optimal position sizing. This addresses the limitation of current metrics that assume zero risk-free rate and lack leverage guidance for strategy implementation.

## What Changes

- Add `risk_free_rate` parameter (default 0.04) to BacktestEngine initialization for proper risk-adjusted calculations
- Confirm Sharpe ratio calculation is properly annualized
- Add Kelly leverage output to metrics using the formula: fi = mi / si² where mi is mean excess return and si is Sharpe ratio
- Update engine and metrics interfaces to support these enhancements

## Capabilities

### New Capabilities
- `backtest-engine-risk-free-rate`: Backtest engine configuration with risk-free rate parameter for accurate excess return calculations
- `metrics-kelly-leverage`: Performance metrics output including Kelly leverage for optimal position sizing

### Modified Capabilities
<!-- No existing capabilities are being modified at the spec level -->

## Impact

- **Code**: `src/tiportfolio/engine.py` (BacktestEngine initialization), `src/tiportfolio/metrics.py` (metrics calculations)
- **APIs**: Engine constructor signature changes (backward compatible with default), metrics function returns additional kelly_leverage field
- **Dependencies**: No new dependencies required
