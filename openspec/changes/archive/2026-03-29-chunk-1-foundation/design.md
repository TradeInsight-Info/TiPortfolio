## Context

TiPortfolio has an approved implementation spec (`2026-03-28-core-engine-implementation-design.md`) and comprehensive API docs, but zero core implementation. The existing codebase has only `helpers/` (data fetching: YFinance, Alpaca, caching). This design covers the first vertical slice — enough to run the Quick Example end-to-end.

The existing `helpers/data.py` returns a flat concatenated DataFrame with a `symbol` column. Our spec requires `dict[str, pd.DataFrame]` keyed by ticker, each with a UTC `DatetimeIndex`. The data layer wraps the existing helpers with a split-and-reindex step.

## Goals / Non-Goals

**Goals:**
- Quick Example from `api/index.md` runs and produces output
- All code is TDD — tests written first, implementation follows
- Public API matches the spec exactly (`ti.Portfolio`, `ti.Signal.Monthly()`, etc.)
- Clean separation: each module has one job, testable in isolation

**Non-Goals:**
- Parent/child portfolio trees (Chunk 3)
- Short selling, carry costs (Chunk 3)
- Or/And/Not branching combinators (Chunk 2)
- Advanced weighting algos (Chunks 2-4)
- Multi-backtest comparison, Trades wrapper, Plotly (Chunk 5)
- Alpaca data source in `fetch_data` (yfinance only for now; Alpaca added later)

## Decisions

### 1. `fetch_data` wraps existing helpers via composition, not inheritance

**Decision:** `fetch_data` instantiates `helpers.data.YFinance()`, calls `.query()`, then splits the flat DataFrame into `dict[str, pd.DataFrame]`.

**Why:** The existing helpers have caching, logging, and error handling that we shouldn't duplicate. Direct wrapping keeps the dependency one-way: `data.py → helpers/data.py`. Never the reverse.

**Alternative considered:** Rewrite data fetching from scratch using `yfinance.download` directly. Rejected — loses caching and would need re-implementation.

### 2. `Signal.Schedule` pre-computes rebalance dates at construction time

**Decision:** `Signal.Schedule.__init__` does NOT pre-compute dates. Instead, `__call__` checks whether `context.date` matches a schedule rule (e.g., last trading day of the month). Uses `pandas_market_calendars` NYSE calendar to resolve trading days.

**Why:** Pre-computation would require knowing the full date range at algo construction time, but algos are constructed before `Backtest` — they don't have access to the date range yet. Lazy evaluation per-bar is simpler and matches how bt works.

**Implementation:** For Monthly with `day="end"`: check if `context.date` is the last trading day of its month by comparing against NYSE calendar's valid days for that month.

### 3. `BacktestResult` implements collection pattern from day one

**Decision:** Even though Chunk 1 only runs single backtests, `BacktestResult` wraps `list[_SingleResult]`. Both `result[0]` and `result["name"]` work.

**Why:** This is the public API contract. If we shipped a simpler wrapper first, Chunk 5 would need a breaking change. Small upfront cost, zero migration cost later.

### 4. `Action.Rebalance` is fully implemented (both leaf and parent paths)

**Decision:** Implement the full `is_parent` check in `Action.Rebalance.__call__`. For Chunk 1, the parent path (`_allocate_children`) callback won't be set on Context, so we raise `RuntimeError` if it's called without the callback. The leaf path works immediately.

**Why:** Avoids re-implementing `Action.Rebalance` in Chunk 3. The code is already in the spec — just implement it. The parent path is dead code until Chunk 3 sets the callback.

### 5. Test fixtures use deterministic CSV data, not network calls

**Decision:** Create `tests/data/prices.csv` with 20 trading days of hand-crafted prices for QQQ, BIL, GLD. All tests use this fixture via `conftest.py`. No network calls in tests.

**Why:** Financial calculations need exact expected values. With known prices (e.g., QQQ closing at 100, 101, 102...), we can compute expected portfolio equity by hand and assert precisely.

### 6. `summary()` returns a pandas DataFrame, not a printed string

**Decision:** `_SingleResult.summary()` returns a `pd.DataFrame` with metric names as index. Printing is left to the caller (or `__repr__`).

**Why:** Returning data is more composable than printing. Users can compare, filter, or export. The bt library does the same.

## Risks / Trade-offs

- **[Risk] Existing helpers may have breaking API changes** → Mitigation: `fetch_data` tests mock the helper call; integration test catches actual breakage.
- **[Risk] `pandas_market_calendars` NYSE calendar may not cover all edge cases (holidays, half-days)** → Mitigation: Use the library as-is; it's battle-tested. Test with known calendar dates.
- **[Risk] TDD overhead slows initial delivery** → Trade-off: Accepted. The financial calculations in the simulation loop are subtle (fee deduction, equity tracking). Tests catch rounding/ordering bugs that would be painful to debug later.
- **[Risk] `summary()` metric formulas may differ from bt** → Mitigation: Use standard formulas from the spec. Document the formula in code. We're not trying to match bt exactly.
