## Context

The TiPortfolio library provides backtesting capabilities for portfolio allocation strategies. Currently, the `compute_metrics` function calculates performance metrics assuming a zero risk-free rate, and does not provide Kelly leverage guidance. The engine classes (ScheduleBasedEngine, VolatilityBasedEngine) initialize without explicit risk-free rate configuration.

This change enhances risk-adjusted performance analysis by allowing configurable risk-free rates and providing Kelly leverage calculations for optimal position sizing.

## Goals / Non-Goals

**Goals:**
- Add `risk_free_rate` parameter (default 0.04) to BacktestEngine initialization
- Ensure Sharpe ratio calculation remains properly annualized
- Add Kelly leverage calculation to metrics output using formula: fi = μ / σ² where μ is annualized mean excess return and σ is annualized standard deviation
- Maintain backward compatibility

**Non-Goals:**
- Changing existing metric calculations beyond adding Kelly leverage
- Adding risk-free rate to individual strategy metrics (only for overall portfolio)
- Modifying existing API signatures without defaults

## Decisions

**Risk-Free Rate Parameter Location**: Add `risk_free_rate` parameter to engine `__init__` methods rather than `run()` methods. This allows configuration at initialization time and can be stored as instance attribute for use in metrics calculation.

**Kelly Leverage Formula**: Use fi = annualized_mean_excess_return / (annualized_std_dev)^2. This follows the Kelly criterion for optimal bet sizing where excess returns are assumed statistically independent.

**Default Value**: Use 0.04 (4%) as default risk-free rate, a reasonable long-term average for major market indices.

**Metrics Return Structure**: Add `kelly_leverage` as a new key in the metrics dictionary, maintaining the existing structure for backward compatibility.

## Risks / Trade-offs

[Default risk-free rate may not match user's expectations] → Users can override with custom value; documentation will clarify the assumption

[Kelly leverage assumes statistical independence of returns] → Add disclaimer in documentation; formula is simplified for independent strategies as stated in requirements

[Additional parameter increases API complexity] → Parameter has sensible default; backward compatible
