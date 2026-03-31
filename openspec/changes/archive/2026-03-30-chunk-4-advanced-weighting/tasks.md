> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Dependencies

- [x] 1.1 Add `riskfolio-lib` to `pyproject.toml` dependencies
- [x] 1.2 Run `uv sync` to install the new dependency

## 2. Weigh.BasedOnBeta Implementation

- [x] 2.1 Write unit tests in `tests/test_weigh_beta.py` — beta computation, convergence to target=0, non-normalised weights, ValueError for insufficient benchmark data, max iterations fallback
- [x] 2.2 Implement `Weigh.BasedOnBeta` class in `src/tiportfolio/algos/weigh.py` — constructor with `initial_ratio`, `target_beta`, `lookback`, `base_data`; beta computation via `Cov/Var`; iterative scaling loop (max 1000 iterations, tolerance 1e-6)
- [x] 2.3 Run `test_weigh_beta.py` and verify all tests pass

## 3. Weigh.ERC Implementation

- [x] 3.1 Write unit tests in `tests/test_weigh_erc.py` — ERC weight computation, weights sum to 1.0, all weights non-negative, covariance methods (ledoit-wolf, hist, oas), ValueError for insufficient data, ValueError for singular covariance
- [x] 3.2 Implement `Weigh.ERC` class in `src/tiportfolio/algos/weigh.py` — constructor with `lookback`, `covar_method`, `risk_parity_method`, `maximum_iterations`, `tolerance`; covariance estimation; riskfolio-lib solver delegation; weight normalisation
- [x] 3.3 Run `test_weigh_erc.py` and verify all tests pass

## 4. Integration & Examples

- [x] 4.1 Add integration tests to `tests/test_e2e.py` for both `Weigh.BasedOnBeta` and `Weigh.ERC` using offline fixture data
- [x] 4.2 Create `examples/08_beta_neutral.py` example script
- [x] 4.3 Create `examples/09_erc_risk_parity.py` example script
- [x] 4.4 Run full test suite (`uv run python -m pytest`) and verify no regressions

## 5. Public API Export

- [x] 5.1 Verify `Weigh.BasedOnBeta` and `Weigh.ERC` are accessible via `ti.Weigh.BasedOnBeta` and `ti.Weigh.ERC` (already nested in `Weigh` class, should work automatically)
