# Chunk 4: Advanced Weighting — Beta Neutral & ERC

**Goal**: Implement `Weigh.BasedOnBeta` (beta-neutral portfolio construction) and `Weigh.ERC` (Equal Risk Contribution / Risk Parity) algorithms.

**Architecture**: Two new `Algo` subclasses in `algos/weigh.py`. BasedOnBeta uses iterative proportional scaling toward a target beta. ERC delegates covariance estimation to pandas/numpy and optimisation to `riskfolio-lib`. Both follow the existing `Algo.__call__(context) -> bool` pattern.

**Tech Stack**: Python 3.12, pandas, numpy, riskfolio-lib (new dependency)

**Spec**: `docs/work-plan/chunk-4-advanced-weighting.md`, `docs/guides/allocation-strategies.md` (Beta Neutral and ERC sections)

## File Map

1. Modify: `src/tiportfolio/algos/weigh.py` — Add `Weigh.BasedOnBeta` and `Weigh.ERC` classes
2. Modify: `pyproject.toml` — Add `riskfolio-lib` dependency
3. Create: `tests/test_weigh_beta.py` — Unit tests for `Weigh.BasedOnBeta`
4. Create: `tests/test_weigh_erc.py` — Unit tests for `Weigh.ERC`
5. Modify: `tests/test_e2e.py` — Add integration tests for both algorithms
6. Create: `examples/08_beta_neutral.py` — Example script for beta-neutral strategy
7. Create: `examples/09_erc_risk_parity.py` — Example script for ERC strategy

## Chunks

### Chunk 1: Weigh.BasedOnBeta — Iterative Proportional Scaling

Implement beta-neutral weighting that scales an initial weight vector to achieve a target portfolio beta (typically 0).

Key design decisions:
- **`base_data: pd.DataFrame`** — benchmark OHLCV data passed directly (same pattern as `Signal.VIX(data=...)`)
- **Weights are NOT normalised** — `sum(w)` can be < 1 (cash residual) or > 1 (leverage)
- **ValueError in `__call__`** — raised if base_data lacks data for the lookback window (not in constructor)
- **Max 1000 iterations** — iterative scaling loop with convergence tolerance

Algorithm:
1. Compute rolling betas for each ticker vs benchmark over lookback window
2. Calculate current portfolio beta: `sum(w_i * beta_i)`
3. Iteratively scale weights to converge toward target beta
4. Stop when `|portfolio_beta - target_beta| < tolerance` or max iterations reached

Files:
- `src/tiportfolio/algos/weigh.py`
- `tests/test_weigh_beta.py`
- `tests/test_e2e.py`
- `examples/08_beta_neutral.py`

Steps:
- Implement beta computation using OLS regression of asset returns vs benchmark returns
- Implement iterative proportional scaling loop (max 1000 iterations, tolerance 1e-6)
- Handle edge cases: insufficient lookback data (ValueError), zero-beta assets, single-asset portfolio
- Write unit tests covering convergence, edge cases, and ValueError scenarios
- Add e2e integration test and example script

### Chunk 2: Weigh.ERC — Equal Risk Contribution (Risk Parity)

Implement risk parity weighting where each asset contributes equally to total portfolio risk, using the full covariance matrix.

Key design decisions:
- **Weights always sum to 1.0** — fully invested, long-only
- **Delegates to riskfolio-lib** — we build the covariance matrix; the solver does optimisation
- **Covariance methods**: `ledoit-wolf` (default), `hist`, `oas`
- **Solver methods**: `ccd` (cyclical coordinate descent, default), `slsqp`

Algorithm:
1. Compute returns over lookback window for selected assets
2. Estimate covariance matrix using chosen method (Ledoit-Wolf shrinkage preferred)
3. Pass covariance matrix to riskfolio-lib's risk parity solver
4. Solver returns weights where marginal risk contribution is equal across all assets

Files:
- `src/tiportfolio/algos/weigh.py`
- `pyproject.toml`
- `tests/test_weigh_erc.py`
- `tests/test_e2e.py`
- `examples/09_erc_risk_parity.py`

Steps:
- Add `riskfolio-lib` to `pyproject.toml` dependencies
- Implement covariance matrix estimation (ledoit-wolf, hist, oas)
- Implement ERC solver wrapper around riskfolio-lib
- Handle edge cases: singular covariance matrix, insufficient data, convergence failure
- Write unit tests with synthetic covariance matrices for deterministic verification
- Add e2e integration test and example script
