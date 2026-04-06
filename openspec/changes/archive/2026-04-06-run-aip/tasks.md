> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Core AIP Engine

- [x] 1.1 Add optional `monthly_aip_amount: float = 0.0`, `total_contributions: float = 0.0`, and `contribution_count: int = 0` parameters to `_SingleResult.__init__()` in `result.py`
- [x] 1.2 Update `_SingleResult.summary()` to include `total_contributions` and `contribution_count` rows when `total_contributions > 0`
- [x] 1.3 Add `monthly_aip_amount: float = 0.0` parameter to `_run_single()` in `backtest.py`. Add month-end detection and cash injection logic (after carry costs, before algo queue). Track `contribution_total` and `contribution_count`. Pass both to `_SingleResult`.
- [x] 1.4 Add `run_aip(*tests, monthly_aip_amount, leverage)` public function in `backtest.py` that calls `_run_single(bt, monthly_aip_amount)` for each backtest and returns `BacktestResult`
- [x] 1.5 Export `run_aip` in `src/tiportfolio/__init__.py` and add to `__all__`

## 2. Tests

- [x] 2.1 Create `tests/test_aip.py` with test: AIP result has correct `total_contributions` and `contribution_count` in summary
- [x] 2.2 Test: AIP final_value > initial_capital + total_contributions for a rising market (using existing test fixtures)
- [x] 2.3 Test: AIP with monthly_aip_amount=0 produces identical result to `run()`
- [x] 2.4 Test: Cash injection happens only on month-end trading days (verify via trade records or equity curve jumps)
- [x] 2.5 Test: `plot()` and `full_summary()` work on AIP result without errors

## 3. Example and Documentation

- [x] 3.1 Create `examples/21_auto_investment_plan.py` showing monthly $1000 AIP into QQQ/BIL/GLD equal-weight strategy
- [x] 3.2 Update `examples/README.md` to list the new example
