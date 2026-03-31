# ERC Weighting

## Purpose

`Weigh.ERC` (Equal Risk Contribution) computes portfolio weights such that each asset contributes equally to the total portfolio risk. It estimates the covariance matrix of returns using configurable shrinkage methods and delegates the optimisation to riskfolio-lib. Output weights are always normalised to sum to 1.0 (fully invested, long-only).

## Requirements

### Requirement: ERC constructor accepts configuration parameters

`Weigh.ERC` SHALL accept the following constructor parameters:
- `lookback: pd.DateOffset` — window for computing the covariance matrix
- `covar_method: str` — covariance estimation method, one of `"ledoit-wolf"` (default), `"hist"`, `"oas"`
- `risk_parity_method: str` — optimisation solver, one of `"ccd"` (default), `"slsqp"`
- `maximum_iterations: int` — max solver iterations (default `100`)
- `tolerance: float` — convergence tolerance (default `1e-8`)

#### Scenario: Default construction
- **WHEN** `Weigh.ERC(lookback=pd.DateOffset(months=3))` is called
- **THEN** the algo instance SHALL use `covar_method="ledoit-wolf"`, `risk_parity_method="ccd"`, `maximum_iterations=100`, `tolerance=1e-8`

#### Scenario: Custom construction
- **WHEN** `Weigh.ERC(lookback=pd.DateOffset(months=6), covar_method="oas", risk_parity_method="slsqp")` is called
- **THEN** the algo instance SHALL use the specified parameters

### Requirement: ERC computes covariance matrix from returns

The algorithm SHALL compute the covariance matrix of daily returns for all selected assets over the lookback window ending at `context.date`.

Covariance estimation methods:
- `"ledoit-wolf"`: Ledoit-Wolf shrinkage estimator
- `"hist"`: Sample covariance (no shrinkage)
- `"oas"`: Oracle Approximating Shrinkage estimator

#### Scenario: Ledoit-Wolf covariance estimation
- **WHEN** `covar_method="ledoit-wolf"` and lookback covers 3 months of daily returns
- **THEN** the covariance matrix SHALL be estimated using the Ledoit-Wolf shrinkage method

#### Scenario: Historical sample covariance
- **WHEN** `covar_method="hist"`
- **THEN** the covariance matrix SHALL be the sample covariance with no shrinkage

### Requirement: ERC delegates optimisation to riskfolio-lib

The algorithm SHALL pass the estimated covariance matrix to riskfolio-lib's risk parity solver to compute weights where each asset's marginal risk contribution is equal.

#### Scenario: CCD solver
- **WHEN** `risk_parity_method="ccd"`
- **THEN** the Cyclical Coordinate Descent solver SHALL be used

#### Scenario: SLSQP solver
- **WHEN** `risk_parity_method="slsqp"`
- **THEN** the Sequential Least Squares Programming solver SHALL be used

### Requirement: ERC weights always sum to 1.0

Output weights SHALL always be normalised to sum to exactly 1.0. The strategy is fully invested, long-only.

#### Scenario: Weight normalisation
- **WHEN** the solver returns weights that sum to 0.9999 due to floating-point precision
- **THEN** `context.weights` SHALL contain weights normalised to sum to 1.0

#### Scenario: All weights are non-negative
- **WHEN** the solver computes ERC weights
- **THEN** all weights SHALL be >= 0 (long-only constraint)

### Requirement: ERC raises ValueError for insufficient data

The algo SHALL raise `ValueError` inside `__call__` if the lookback window contains fewer than 2 observations for any selected asset (insufficient to compute covariance).

#### Scenario: Insufficient return data
- **WHEN** `context.date = 2024-02-01`, `lookback = pd.DateOffset(months=3)`, and price data for an asset starts at 2024-01-15
- **THEN** a `ValueError` SHALL be raised indicating insufficient data for covariance estimation

### Requirement: ERC raises ValueError for singular covariance matrix

The algo SHALL raise `ValueError` if the covariance matrix is singular or the solver fails to converge within `maximum_iterations`.

#### Scenario: Singular covariance
- **WHEN** two assets have perfectly correlated returns producing a singular covariance matrix
- **THEN** a `ValueError` SHALL be raised

#### Scenario: Solver non-convergence
- **WHEN** the solver does not converge within `maximum_iterations`
- **THEN** a `ValueError` SHALL be raised

### Requirement: ERC writes weights to context

After computation, the algo SHALL write the final weight dict to `context.weights` and return `True`.

#### Scenario: Weights written to context
- **WHEN** the algo successfully computes ERC weights for assets ["SPY", "TLT", "GLD", "BIL"]
- **THEN** `context.weights` SHALL be a `dict[str, float]` with keys for each selected asset and values summing to 1.0
