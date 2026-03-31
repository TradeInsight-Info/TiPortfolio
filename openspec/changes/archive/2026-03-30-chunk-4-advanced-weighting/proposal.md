## Why

TiPortfolio currently offers equal-weight, ratio, and volatility-targeting weighting. Portfolio managers need two additional mathematically-grounded strategies: **beta-neutral** (hedge market exposure to a target beta, typically zero) and **Equal Risk Contribution** (size positions so every asset contributes the same amount of risk). These complete the weighting toolkit described in the allocation-strategies guide and unblock the Chunk 4 work-plan deliverables.

## What Changes

- Add `Weigh.BasedOnBeta(initial_ratio, target_beta, lookback, base_data)` — iterative proportional scaling of weights toward a target portfolio beta. Weights are **not** normalised; `sum(w) < 1` implies a cash residual.
- Add `Weigh.ERC(lookback, covar_method, risk_parity_method, maximum_iterations, tolerance)` — covariance-aware risk parity via riskfolio-lib. Weights always sum to 1.0 (fully invested, long-only).
- Add `riskfolio-lib` as a new dependency in `pyproject.toml`.
- Add example scripts (`08_beta_neutral.py`, `09_erc_risk_parity.py`) and integration tests.

## Capabilities

### New Capabilities

- `beta-neutral-weighting`: Iterative weight scaling to achieve a target portfolio beta against an external benchmark. Covers beta computation, convergence loop, and ValueError semantics.
- `erc-weighting`: Equal Risk Contribution (Risk Parity) weighting using covariance estimation and riskfolio-lib optimisation. Covers covariance methods (ledoit-wolf, hist, oas), solver methods (ccd, slsqp), and weight normalisation.

### Modified Capabilities

_(none — no existing spec requirements change)_

## Impact

- **Code**: `src/tiportfolio/algos/weigh.py` gains two new inner classes
- **Dependencies**: `riskfolio-lib` added to `pyproject.toml` (brings numpy/scipy transitively)
- **Tests**: New test files `test_weigh_beta.py`, `test_weigh_erc.py`; extended `test_e2e.py`
- **Examples**: Two new example scripts
- **Public API**: Two new algo classes exposed via `ti.Weigh.BasedOnBeta` and `ti.Weigh.ERC`
