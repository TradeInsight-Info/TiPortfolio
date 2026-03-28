# Chunk 4: Advanced Weighting

**Goal:** Implement the mathematically complex weighing algos.

**Depends on:** Chunk 3

## Deliverable

Beta Neutral and ERC examples from `allocation-strategies.md` work.

```python
import pandas as pd
import tiportfolio as ti

# Beta Neutral
tickers = ["QQQ", "BIL", "GLD"]
data = ti.fetch_data(tickers, start="2019-01-01", end="2024-12-31")
spy_data = ti.fetch_data(["SPY"], start="2019-01-01", end="2024-12-31")

portfolio = ti.Portfolio('beta_neutral', [
    ti.Signal.Monthly(),
    ti.Select.All(),
    ti.Weigh.BasedOnBeta(
        initial_ratio={"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1},
        target_beta=0,
        lookback=pd.DateOffset(months=1),
        base_data=spy_data["SPY"],
    ),
    ti.Action.Rebalance(),
], tickers)

# ERC (Risk Parity)
erc_portfolio = ti.Portfolio('erc', [
    ti.Signal.Monthly(),
    ti.Select.All(),
    ti.Weigh.ERC(
        lookback=pd.DateOffset(months=3),
        covar_method="ledoit-wolf",
        risk_parity_method="ccd",
    ),
    ti.Action.Rebalance(),
], ["SPY", "TLT", "GLD", "BIL"])
```

## Files to Modify

| File | Change |
|------|--------|
| `algos/weigh.py` | Add `Weigh.BasedOnBeta(initial_ratio, target_beta, lookback, base_data)` — iterative proportional scaling toward target beta. Add `Weigh.ERC(lookback, covar_method, risk_parity_method, maximum_iterations, tolerance)` — delegates to riskfolio-lib for risk parity optimisation. |
| `pyproject.toml` | Add `riskfolio-lib` as dependency |

## Spec Sections Covered

- Section 5: Weigh.BasedOnBeta algorithm (beta computation, iterative scaling, max 1000 iterations)
- Section 5: Weigh.ERC algorithm (covariance estimation, CCD/SLSQP solver, ledoit-wolf/hist/oas)

## Key Design Decisions (from spec)

- **BasedOnBeta receives `base_data: pd.DataFrame`** — the benchmark OHLCV data passed directly, not a ticker string. Same pattern as `Signal.VIX(data=...)`.
- **BasedOnBeta weights are not normalised** — scale factor represents leverage/de-leverage. Cash residual when `sum(w) < 1`.
- **BasedOnBeta ValueError**: Raised inside `__call__` (not constructor) if `base_data` is missing data for the lookback window.
- **ERC weights always sum to 1.0** — fully invested, long-only.
- **ERC delegates to riskfolio-lib** — we build the covariance matrix; the solver does the optimisation.
