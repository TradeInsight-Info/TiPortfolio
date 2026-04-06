# Auto Investment Plan (AIP) — run_aip

**Goal**: Add a `run_aip` function that simulates dollar-cost averaging (DCA) / auto investment plans — injecting a fixed amount of cash into the portfolio at regular intervals and buying according to the current allocation.
**Architecture**: New `run_aip()` function alongside existing `run()`, reusing the same simulation loop with cash injection at month-end boundaries. Returns `BacktestResult` with identical `summary()`/`plot()` interface.
**Tech Stack**: Python, pandas, existing TiPortfolio engine (backtest.py, result.py)
**Spec**: `openspec/specs/run-aip/spec.md`

## File Map:

1. Modify : `src/tiportfolio/backtest.py` - Add `run_aip()` function and `_run_single_aip()` simulation loop with monthly cash injection
2. Modify : `src/tiportfolio/__init__.py` - Export `run_aip` in public API
3. Create : `tests/test_aip.py` - Unit tests for AIP functionality
4. Create : `examples/21_auto_investment_plan.py` - Example script demonstrating AIP usage
5. Modify : `docs/api/index.md` - Document run_aip in API reference (if exists)


## Chunks

### Chunk 1: Core AIP engine
Add the `run_aip()` function and internal `_run_single_aip()` that modifies the daily simulation loop to inject cash at month-end boundaries before the algo stack fires.

Files:
- `src/tiportfolio/backtest.py` — add `_run_single_aip()` and `run_aip()`
- `src/tiportfolio/__init__.py` — export `run_aip`
Steps:
- Step 1: Create `_run_single_aip(backtest, monthly_amount)` that clones the `_run_single()` loop but adds cash injection at each month-end trading day
- Step 2: Create `run_aip(*tests, monthly_aip_amount, leverage)` public function that calls `_run_single_aip()` and returns `BacktestResult`
- Step 3: Cash injection logic: on last trading day of each month, add `monthly_aip_amount` to root portfolio's cash before the algo queue fires

### Chunk 2: Tests and example
Write tests covering AIP behavior and a runnable example script.

Files:
- `tests/test_aip.py`
- `examples/21_auto_investment_plan.py`
Steps:
- Step 1: Test that final equity > initial_capital + total_contributions for a rising market
- Step 2: Test that contributions happen at correct month-end dates
- Step 3: Test that summary/plot work identically to regular backtest results
- Step 4: Create example script showing AIP with monthly $1000 into QQQ/BIL/GLD
