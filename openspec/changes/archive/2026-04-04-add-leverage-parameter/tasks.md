> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Tests First (TDD)

- [x] 1.1 Create `tests/test_leverage.py` with tests: default leverage=1.0 produces identical results, leverage=2.0 scales daily returns and deducts borrowing cost (`(factor-1) × loan_rate / bars_per_year` per day), list of floats applies per-backtest, mismatched list length raises ValueError, leverage=1.0 leaves name unchanged, leverage!=1.0 appends "(2.0x)" suffix, summary includes leverage row, higher leverage incurs proportionally higher borrowing cost
- [x] 1.2 Run tests and confirm they fail (red phase)

## 2. Core Implementation

- [x] 2.1 Add `_apply_leverage(result: _SingleResult, factor: float, config: TiConfig) -> _SingleResult` helper in `backtest.py` — scales daily returns by factor, deducts daily borrowing cost `(factor-1) × config.loan_rate / config.bars_per_year`, rebuilds equity curve, returns new `_SingleResult` with modified equity and leverage metadata
- [x] 2.2 Update `run()` signature to `def run(*tests: Backtest, leverage: float | list[float] = 1.0) -> BacktestResult` — validate leverage input, normalize single float to list, apply per-backtest after `_run_single()`
- [x] 2.3 Add `leverage: float = 1.0` field to `_SingleResult.__init__` — store the applied leverage factor

## 3. Result Display

- [x] 3.1 Update `_SingleResult.summary()` to include `leverage` in the output DataFrame
- [x] 3.2 Update `_SingleResult.full_summary()` to include `leverage` in the output DataFrame
- [x] 3.3 Apply name suffix logic: when leverage != 1.0, append " ({factor}x)" to result name

## 4. Example

- [x] 4.1 Create `examples/21_leverage_comparison.py` — monthly rebalance QQQ/BIL/GLD at start-of-month with fixed weights 0.7/0.2/0.1, compare at 1x, 1.5x, and 2x leverage using `run(bt1, bt2, bt3, leverage=[1.0, 1.5, 2.0])`, show summary comparison and plot

## 5. Verification

- [x] 5.1 Run all tests and confirm they pass (green phase)
- [x] 5.2 Run existing test suite to confirm no regressions
