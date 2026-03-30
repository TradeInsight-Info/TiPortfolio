## ADDED Requirements

### Requirement: Weigh.BasedOnHV scales weights to target annualised portfolio volatility
`Weigh.BasedOnHV` SHALL accept `initial_ratio: dict[str, float]`, `target_hv: float` (annualised decimal), and `lookback: pd.DateOffset`. It SHALL compute each ticker's annualised historical volatility, approximate portfolio HV using diagonal covariance, and scale all weights by `target_hv / portfolio_hv`.

#### Scenario: Scale down high-volatility portfolio
- **WHEN** `BasedOnHV(initial_ratio={"QQQ": 0.7, "BIL": 0.3}, target_hv=0.10, lookback=DateOffset(months=1))` is called and the portfolio's realised HV is 0.20
- **THEN** `context.weights` are approximately `{"QQQ": 0.35, "BIL": 0.15}` (scale factor ≈ 0.5)

#### Scenario: Scale up low-volatility portfolio
- **WHEN** the same algo is called and portfolio HV is 0.05
- **THEN** `context.weights` are approximately `{"QQQ": 1.4, "BIL": 0.6}` (scale factor ≈ 2.0, leverage)

### Requirement: Weigh.BasedOnHV weights are not normalised
Scaled weights SHALL NOT be normalised to sum to 1.0. Scale factor > 1 represents leverage; < 1 represents cash residual.

#### Scenario: Leverage weights sum exceeds 1.0
- **WHEN** scale factor is 2.0 and initial weights sum to 1.0
- **THEN** `context.weights` values sum to 2.0 (leveraged position)

#### Scenario: De-leveraged weights sum below 1.0
- **WHEN** scale factor is 0.5 and initial weights sum to 1.0
- **THEN** `context.weights` values sum to 0.5 (cash residual of 0.5)

### Requirement: Weigh.BasedOnHV uses config.bars_per_year for annualisation
The volatility annualisation formula SHALL be `hv = daily_returns.std() * sqrt(context.config.bars_per_year)`.

#### Scenario: Custom bars_per_year
- **WHEN** `context.config.bars_per_year` is 252
- **THEN** daily std is multiplied by `sqrt(252)` to get annualised HV

### Requirement: Weigh.BasedOnHV handles zero-volatility gracefully
When portfolio HV is zero (all flat prices), the algo SHALL return `initial_ratio` unchanged (no scaling).

#### Scenario: All prices flat
- **WHEN** all tickers have constant close prices over the lookback window
- **THEN** `context.weights` equals `initial_ratio` (portfolio_hv is 0, division avoided)

### Requirement: Weigh.BasedOnHV target_hv is annualised decimal
`target_hv` SHALL be expressed as an annualised decimal (e.g., 0.15 for 15% vol). No validation SHALL be applied for values > 1.0.

#### Scenario: Decimal input
- **WHEN** `target_hv=0.15` is passed
- **THEN** the algo targets 15% annualised portfolio volatility

### Requirement: Weigh.BasedOnHV returns True
`Weigh.BasedOnHV.__call__` SHALL always return `True`.

#### Scenario: Always continues queue
- **WHEN** `Weigh.BasedOnHV` is called
- **THEN** it returns `True`
