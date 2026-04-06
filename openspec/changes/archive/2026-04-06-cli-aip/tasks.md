> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [x]) syntax for tracking.

## 1. CLI Changes

- [x] 1.1 Add `--aip` option (type=float, default=None) to `shared_options` decorator in `cli.py`
- [x] 1.2 Add `aip` parameter to `_run_backtest()` function signature
- [x] 1.3 Add conditional: when `aip` is provided, call `ti.run_aip(..., monthly_aip_amount=aip)` instead of `ti.run(...)` — handle both single and multi-leverage cases

## 2. Tests

- [x] 2.1 Create `tests/test_cli_aip.py` with test: `monthly --aip 1000` produces output containing `total_contributions`
- [x] 2.2 Test: `monthly` without `--aip` does NOT contain `total_contributions` in output
- [x] 2.3 Test: `--aip` works with `--leverage`
- [x] 2.4 Test: `--aip` appears in `--help` output
