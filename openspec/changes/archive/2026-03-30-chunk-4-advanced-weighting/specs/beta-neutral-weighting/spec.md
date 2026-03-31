## ADDED Requirements

### Requirement: BasedOnBeta constructor accepts configuration parameters

`Weigh.BasedOnBeta` SHALL accept the following constructor parameters:
- `initial_ratio: dict[str, float]` — starting weight allocation per ticker
- `target_beta: float` — target portfolio beta (typically 0 for beta-neutral)
- `lookback: pd.DateOffset` — window for computing rolling betas
- `base_data: pd.DataFrame` — benchmark OHLCV DataFrame (e.g., SPY), passed directly

#### Scenario: Valid construction
- **WHEN** `Weigh.BasedOnBeta(initial_ratio={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1}, target_beta=0, lookback=pd.DateOffset(months=1), base_data=spy_df)` is called
- **THEN** the algo instance SHALL be created without error

### Requirement: BasedOnBeta computes per-asset beta against benchmark

The algorithm SHALL compute each asset's beta as `Cov(r_asset, r_benchmark) / Var(r_benchmark)` using daily returns over the lookback window ending at `context.date`.

#### Scenario: Beta computation over lookback window
- **WHEN** the algo is called with `context.date = 2024-06-01` and `lookback = pd.DateOffset(months=1)`
- **THEN** betas SHALL be computed using daily returns from 2024-05-01 to 2024-06-01 for each selected asset vs the benchmark

### Requirement: BasedOnBeta iteratively scales weights toward target beta

The algorithm SHALL use iterative proportional scaling to adjust `initial_ratio` weights until `|portfolio_beta - target_beta| < tolerance` or `maximum_iterations` is reached. Default tolerance SHALL be `1e-6`. Default maximum iterations SHALL be `1000`.

Portfolio beta is defined as `sum(w_i * beta_i)` for all assets.

#### Scenario: Convergence to target beta of 0
- **WHEN** initial weights produce a positive portfolio beta and `target_beta=0`
- **THEN** the algorithm SHALL reduce weights on high-beta assets and increase weights on low/negative-beta assets until portfolio beta is within tolerance of 0

#### Scenario: Maximum iterations reached
- **WHEN** the algorithm does not converge within 1000 iterations
- **THEN** the best weights found so far SHALL be used and the algo SHALL return `True`

### Requirement: BasedOnBeta weights are NOT normalised

Output weights SHALL NOT be normalised to sum to 1.0. When `sum(weights) < 1.0`, the residual represents a cash position. When `sum(weights) > 1.0`, the excess represents leverage.

#### Scenario: Cash residual
- **WHEN** target beta scaling produces weights summing to 0.85
- **THEN** `context.weights` SHALL contain weights summing to 0.85 (not normalised to 1.0)

### Requirement: BasedOnBeta raises ValueError for insufficient benchmark data

The algo SHALL raise `ValueError` inside `__call__` (not the constructor) if `base_data` does not contain sufficient data for the lookback window ending at `context.date`.

#### Scenario: Missing benchmark data for lookback
- **WHEN** `context.date = 2024-02-01`, `lookback = pd.DateOffset(months=3)`, and `base_data` only has data from 2024-01-01
- **THEN** a `ValueError` SHALL be raised with a message indicating insufficient benchmark data

#### Scenario: Sufficient benchmark data
- **WHEN** `base_data` covers the full lookback window
- **THEN** no error SHALL be raised and weights SHALL be computed normally

### Requirement: BasedOnBeta writes weights to context

After computation, the algo SHALL write the final weight dict to `context.weights` and return `True`.

#### Scenario: Weights written to context
- **WHEN** the algo successfully computes weights
- **THEN** `context.weights` SHALL be a `dict[str, float]` mapping selected tickers to their adjusted weights
