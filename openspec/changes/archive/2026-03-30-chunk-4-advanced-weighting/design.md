## Context

TiPortfolio's `Weigh` namespace currently has three algorithms: `Equally`, `Ratio`, and `BasedOnHV`. All follow the same `Algo.__call__(context: Context) -> bool` pattern, reading from `context.selected` and `context.prices`, writing to `context.weights`.

This change adds two mathematically heavier algorithms that introduce new concerns: external benchmark data (BasedOnBeta) and a third-party optimisation library (ERC via riskfolio-lib).

## Goals / Non-Goals

**Goals:**
- Implement `Weigh.BasedOnBeta` with iterative proportional scaling toward a target beta
- Implement `Weigh.ERC` with covariance-aware risk parity optimisation
- Follow existing patterns: inner classes of `Weigh`, same `__call__` signature, same `context.prices` data access
- Add `riskfolio-lib` as the sole new dependency

**Non-Goals:**
- No changes to `Context`, `Algo`, or `AlgoQueue` abstractions
- No custom optimisation solvers — delegate entirely to riskfolio-lib for ERC
- No multi-factor beta models — single-benchmark beta only
- No transaction cost awareness in the weighting algorithms (that's the engine's job)

## Decisions

### 1. Beta computation: OLS regression over lookback window

**Choice**: Compute beta as `Cov(r_asset, r_benchmark) / Var(r_benchmark)` using daily returns over the lookback window.

**Alternatives considered**:
- Rolling beta via `pandas.DataFrame.rolling` — unnecessary overhead since we only need one beta per rebalance date
- EWMA-weighted beta — adds complexity; standard OLS matches the spec

**Rationale**: Simple, well-understood, matches the spec. The lookback parameter already controls recency weighting.

### 2. BasedOnBeta iterative scaling algorithm

**Choice**: Proportional scaling — multiply all weights by `target_beta / current_portfolio_beta` ratio, then iterate until convergence.

Each iteration:
1. Compute per-asset beta
2. Portfolio beta = `sum(w_i * beta_i)`
3. Scale factor = `target_beta / portfolio_beta` (when target ≠ 0) or additive adjustment (when target = 0)
4. Update weights: `w_i *= scale_factor`

**For target_beta = 0**: Use additive adjustment — subtract excess beta proportionally from highest-beta assets.

**Convergence**: `|portfolio_beta - target_beta| < 1e-6` or 1000 iterations.

### 3. BasedOnBeta does NOT normalise weights

**Choice**: Output weights can sum to any value. `sum(w) < 1` means cash residual; `sum(w) > 1` means leverage.

**Rationale**: This is explicit in the spec. The engine handles cash/leverage accounting. Normalising would destroy the beta-targeting property.

### 4. ERC covariance estimation

**Choice**: Build the covariance matrix ourselves from returns, then pass to riskfolio-lib.

Three methods:
- `ledoit-wolf` (default): Shrinkage estimator via `sklearn.covariance.LedoitWolf`
- `hist`: Sample covariance via `pandas.DataFrame.cov()`
- `oas`: Oracle Approximating Shrinkage via `sklearn.covariance.OAS`

**Rationale**: riskfolio-lib expects a covariance matrix as input. Using sklearn for shrinkage estimators is standard and avoids reimplementing Ledoit-Wolf.

### 5. ERC solver delegation

**Choice**: Pass covariance matrix to `riskfolio-lib.RiskFunctions` for risk parity optimisation.

Two methods:
- `ccd` (default): Cyclical Coordinate Descent — fast, reliable for ERC
- `slsqp`: Sequential Least Squares Programming — more general, slower

**Rationale**: riskfolio-lib is a well-tested library specifically designed for portfolio optimisation. No benefit to reimplementing CCD/SLSQP ourselves.

### 6. Error handling strategy

**Choice**:
- `BasedOnBeta`: Raise `ValueError` in `__call__` if benchmark data doesn't cover the lookback window
- `ERC`: Raise `ValueError` if covariance matrix is singular or solver doesn't converge
- Both: Return `True` with fallback to `initial_ratio` (BasedOnBeta) or equal weights (ERC) when non-critical issues occur (e.g., insufficient data for one asset)

## Risks / Trade-offs

- **[riskfolio-lib dependency weight]** → riskfolio-lib pulls in scipy, cvxpy, and sklearn transitively. Mitigation: these are standard scientific Python packages already common in quant workflows. Consider making it an optional dependency in future if install size becomes a concern.
- **[Beta convergence for target=0]** → When target beta is exactly 0, multiplicative scaling doesn't work (can't divide by 0). Mitigation: use additive adjustment for zero-target case.
- **[Covariance estimation with few observations]** → Short lookback windows may produce unreliable covariance estimates. Mitigation: Ledoit-Wolf shrinkage is the default, which handles small-sample estimation well.
- **[Numerical precision in ERC]** → Risk parity weights may not sum to exactly 1.0 due to floating-point arithmetic. Mitigation: normalise final weights to sum to 1.0 after solver returns.
