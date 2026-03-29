> Steps use checkbox (- [x]) syntax for tracking.

## 1. Remove fee_per_share from Backtest

- [x] 1.1 Remove `fee_per_share` parameter from `Backtest.__init__` in `src/tiportfolio/backtest.py`
- [x] 1.2 Update `tests/test_backtest.py` — remove `test_fee_override`, update any tests using `fee_per_share` in Backtest
- [x] 1.3 Update `examples/02_custom_config.py` — use `TiConfig(fee_per_share=...)` instead of `Backtest(fee_per_share=...)`
- [x] 1.4 Update `docs/api/index.md` — remove `fee_per_share` from Backtest signature
- [x] 1.5 Update spec `docs/superpowers/specs/2026-03-28-core-engine-implementation-design.md` — remove fee_per_share from Backtest constructor

## 2. Add Signal.Once + buy-and-hold example

- [x] 2.1 Write tests for `Signal.Once` in `tests/test_signal.py` — first call True, subsequent False, buy-and-hold pattern
- [x] 2.2 Implement `Signal.Once` in `src/tiportfolio/algos/signal.py`
- [x] 2.3 Write `examples/06_buy_and_hold.py` — buy-and-hold QQQ/BIL/GLD using Signal.Once

## 3. Verify

- [x] 3.1 Run full test suite — all tests pass
