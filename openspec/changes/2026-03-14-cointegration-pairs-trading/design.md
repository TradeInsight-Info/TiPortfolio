## Context

The current volatility-based dynamic weighting approach uses empirical ratios that may not capture the true long-term equilibrium relationship between paired assets. While successful in reducing portfolio beta, this method lacks the mathematical rigor of cointegration analysis which directly tests for and quantifies long-run relationships between time series.

Cointegration theory provides a statistically sound framework for pairs trading by identifying assets that share a common stochastic trend. The Johansen test specifically offers advantages over simpler Engle-Granger methods by handling multiple cointegrating relationships and providing precise hedge ratios through eigenvector analysis.

## Goals / Non-Goals

**Goals:**
- Implement cointegration-based pairs trading using Johansen test for hedge ratio calculation
- Achieve Sharpe Ratio of 1.0 between 2018-2024 using statistical arbitrage
- Use log prices for mathematically sound cointegration analysis
- Implement Z-score based signal generation with configurable thresholds
- Create event-driven backtesting approach (evaluate vs current ScheduleBasedEngine)
- Start with KO/PEP hardcoded pair prototype before dynamic screening

**Non-Goals:**
- Replacing existing volatility-based strategies (this is additive)
- Implementing complex multi-asset cointegration (focus on pairs initially)
- Real-time trading execution (focus on backtesting and analysis)
- Machine learning approaches (stick to statistical cointegration)

## Decisions

**Mathematical Framework**
- Use `statsmodels.tsa.vector_ar.vecm.coint_johansen` for cointegration testing
- Transform prices to log space: `log_price = ln(price)` for stationarity
- Calculate hedge ratio from first eigenvector: `hedge_ratio = eigenvector[0] / eigenvector[1]`
- Spread calculation: `spread = log_price_A - hedge_ratio * log_price_B`

**Signal Generation**
- Z-score normalization: `z_score = (spread - spread_mean) / spread_std`
- Entry thresholds: `z_score > 2.0` (short spread) or `z_score < -2.0` (long spread)
- Exit threshold: `z_score crosses 0` (mean reversion)
- Rolling window for mean/std calculation (configurable, default 252 days)

**Architecture Evaluation**
- Current ScheduleBasedEngine may not suit event-driven signal trading
- Evaluate need for SignalBasedEngine or EventDrivenEngine
- Prototype in notebook first to determine architectural requirements
- Maintain compatibility with existing backtest infrastructure

**Data Requirements**
- Daily OHLC price data for cointegration testing
- Minimum 2 years of data for reliable cointegration analysis
- Use existing data fetching infrastructure (Alpaca/YFinance)

## Risks / Trade-offs

**Computational Complexity** → Johansen test calculations
- Risk: More intensive than simple volatility ratios
- Mitigation: Cache hedge ratios, recalculate only on rebalance or significant regime change

**Model Assumptions** → Linear cointegration relationships
- Risk: Real-world relationships may be non-linear or time-varying
- Mitigation: Monitor cointegration test statistics, implement regime detection

**Event-Driven Architecture** → Potential engine redesign
- Risk: Current ScheduleBasedEngine may not support signal-based trading
- Mitigation: Prototype in notebook first, evaluate hybrid approaches

**Overfitting Risk** → Parameter optimization
- Risk: Z-score thresholds and lookback windows may be over-optimized
- Mitigation: Use standard statistical thresholds, test across different time periods

**Data Quality** → Cointegration sensitivity to data issues
- Risk: Missing data, survivorship bias may affect cointegration tests
- Mitigation: Use existing data validation, implement robust error handling
