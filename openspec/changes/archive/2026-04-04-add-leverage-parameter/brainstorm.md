# Add Leverage Parameter to `run()`

**Goal**: Allow users to apply leverage multipliers to backtests via `ti.run()` for leveraged comparisons and single-portfolio metrics.
**Architecture**: Add `leverage` parameter to `run()` that scales equity curves post-simulation, keeping the core engine untouched.
**Tech Stack**: Python 3.12, pandas, existing TiPortfolio backtest engine
**Spec**: `openspec/changes/add-leverage-parameter/specs/`

## File Map:

1. Modify : `src/tiportfolio/backtest.py` - Add `leverage` parameter to `run()`, apply scaling in `_run_single()` or post-result
2. Modify : `src/tiportfolio/result.py` - Store leverage metadata in `_SingleResult` for display in summaries
3. Modify : `src/tiportfolio/__init__.py` - No change needed, `run` already exported
4. Create : `tests/test_leverage.py` - Unit tests for leverage parameter behavior
5. Modify : `tests/conftest.py` - Add leverage-related fixtures if needed

## Chunks

### Chunk 1: Core leverage parameter in `run()`
Add `leverage` parameter to `run()` that accepts `float | list[float]`. Default is `1.0` (no leverage). When a single float is given, apply to all backtests. When a list is given, apply each element to the corresponding backtest. Leverage scales the daily returns of the equity curve: `leveraged_return = leverage * unleveraged_return`.

Files:
- `src/tiportfolio/backtest.py`
Steps:
- Add `leverage` param to `run()` signature: `def run(*tests: Backtest, leverage: float | list[float] = 1.0)`
- Validate leverage input (must match number of tests if list)
- After `_run_single()`, apply leverage to each result's equity curve
- Create helper `_apply_leverage(result, leverage_factor)` that rebuilds equity from scaled daily returns

### Chunk 2: Result metadata and display
Store the leverage factor in `_SingleResult` so summaries can display it and the portfolio name can indicate leverage.

Files:
- `src/tiportfolio/result.py`
- `src/tiportfolio/backtest.py`
Steps:
- Add `leverage` field to `_SingleResult.__init__`
- Append leverage suffix to result name (e.g., "Portfolio (2.0x)") when leverage != 1.0
- Include leverage in `summary()` output

### Chunk 3: Tests
Write tests covering: default leverage=1 (no change), single float applied to all, list of floats per-backtest, validation errors for mismatched list length.

Files:
- `tests/test_leverage.py`
Steps:
- Test `run(bt, leverage=1.0)` produces identical results to `run(bt)`
- Test `run(bt, leverage=2.0)` doubles daily returns (approximately doubles CAGR impact)
- Test `run(bt1, bt2, leverage=[1.5, 2.0])` applies different leverage per backtest
- Test `run(bt1, bt2, leverage=[1.5])` raises ValueError (length mismatch)
