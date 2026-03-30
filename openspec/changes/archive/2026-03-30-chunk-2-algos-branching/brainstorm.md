# Chunk 2: More Algos + Branching

**Goal**: Expand the algo catalogue with branching combinators (`Or`, `And`, `Not`), new signal/select/weigh algos, and complete `Signal.Schedule` integer day support — enabling quarterly rebalance, momentum selection, custom weight ratios, and volatility-targeted weighting.

**Architecture**: Plugin-style algo expansion — all new code is `Algo` subclasses that slot into the existing `AlgoQueue` → `Context` pipeline. No engine (`backtest.py`) changes required. Branching combinators live in `algo.py` alongside `AlgoQueue`; new algos extend their respective namespace files.

**Tech Stack**: Python 3.12, pandas, pandas-market-calendars (NYSE calendar for Schedule), numpy (for BasedOnHV volatility math)

**Spec**: `docs/superpowers/specs/2026-03-28-core-engine-implementation-design.md` — Sections 2 (combinators) and 5 (algo catalogue)

## File Map

1. Modify: `src/tiportfolio/algo.py` — Add `Or`, `And`, `Not` combinator classes
2. Modify: `src/tiportfolio/__init__.py` — Export `Or`, `And`, `Not` at `ti.*` level
3. Modify: `src/tiportfolio/algos/signal.py` — Add `Signal.Quarterly`; complete `Signal.Schedule` integer day support
4. Modify: `src/tiportfolio/algos/select.py` — Add `Select.Momentum`, `Select.Filter`
5. Modify: `src/tiportfolio/algos/weigh.py` — Add `Weigh.Ratio`, `Weigh.BasedOnHV`
6. Create: `tests/test_combinators.py` — Unit tests for `Or`, `And`, `Not`
7. Modify: `tests/test_signal.py` — Tests for `Quarterly`, `Schedule(day=int)`
8. Modify: `tests/test_select.py` — Tests for `Momentum`, `Filter`
9. Modify: `tests/test_weigh.py` — Tests for `Ratio`, `BasedOnHV`
10. Modify: `tests/test_e2e.py` — Extend public API import checks for new exports

## Chunks

### Chunk A: Branching Combinators (`Or`, `And`, `Not`)

Foundation for everything else — `Signal.Quarterly` depends on `Or`. These are simple `Algo` subclasses with clear semantics matching Python's `any()`, `all()`, and `not`.

Key decisions:
- `Or` short-circuits on first `True` (mirrors `any()`)
- `And` short-circuits on first `False` (mirrors `all()` — same as `AlgoQueue` but nestable)
- `Not` inverts a single algo's return value
- All accept `Algo` instances (not callables) — type-safe composition
- Side effects matter: `Or` stops calling after first `True`, so later algos' `context` mutations don't happen. This is intentional and matches spec.

Files:
- `src/tiportfolio/algo.py` — Add three classes
- `src/tiportfolio/__init__.py` — Add `Or`, `And`, `Not` to `__all__`
- `tests/test_combinators.py` — Create with tests for truth tables, short-circuit behavior, nesting

Steps:
- Implement `Or`, `And`, `Not` in `algo.py`
- Export from `__init__.py`
- Write tests covering: basic truth tables (T/T, T/F, F/T, F/F), short-circuit verification, nested composition (`Or(And(...), Not(...))`)

### Chunk B: Signal Expansion (`Quarterly`, `Schedule` day=int)

Complete the time-based signal catalogue. `Quarterly` composes `Or` from Chunk A.

Key decisions:
- `Schedule(day=int)` resolves to an actual NYSE trading day. If `day=15` is not a trading day and `next_trading_day=True`, snap forward to the next valid trading day in the same month. If `next_trading_day=False`, return `False` for that month (no signal fires).
- `Quarterly(months=[2,5,8,11])` defaults to Feb/May/Aug/Nov end-of-month — matches typical quarterly rebalance dates. The `months` parameter is customisable.
- `Quarterly` delegates to `Or(*[Schedule(month=m, day=day) for m in months])` — clean composition.

Files:
- `src/tiportfolio/algos/signal.py` — Modify `Schedule.__call__` for int day; add `Quarterly`
- `tests/test_signal.py` — Add tests for day=int (trading day, non-trading day, next_trading_day flag), Quarterly (default months, custom months, fires exactly 4x/year)

Steps:
- Implement `Schedule(day=int)` logic with NYSE calendar lookup
- Implement `Quarterly` class using `Or` composition
- Write tests for both

### Chunk C: Selection Expansion (`Momentum`, `Filter`)

Add data-driven selection algos. Both operate on `context.selected` (set by a prior `Select.All` or similar).

Key decisions:
- `Momentum` computes total return (cumulative `pct_change().sum()`) not log return — simpler, matches spec. Only operates on string tickers (not Portfolio children). The `lag` parameter offsets the lookback end to avoid look-ahead bias.
- `Filter` is a boolean gate — it returns `True`/`False` to continue/halt the queue. It does NOT modify `context.selected`. This is important: if the filter fails, the entire algo queue short-circuits and no rebalance happens (positions hold).
- `Filter.condition` receives a dict of `pd.Series` (one row per ticker from the extra data), not DataFrames. User writes a simple lambda.

Files:
- `src/tiportfolio/algos/select.py` — Add `Momentum`, `Filter`
- `tests/test_select.py` — Tests for Momentum (top-2 of 3, sort order, lag), Filter (pass/fail, halts queue)

Steps:
- Implement `Momentum` with lookback slicing and ranking
- Implement `Filter` with condition callback
- Write tests using synthetic price fixtures

### Chunk D: Weighting Expansion (`Ratio`, `BasedOnHV`)

Add explicit and volatility-targeted weighting algos.

Key decisions:
- `Ratio` normalises to `sum(|w|) = 1.0` — always fully invested. Tickers in `selected` but not in `weights` dict get weight 0 (position closed). This is spec-defined behavior.
- `BasedOnHV` scales `initial_ratio` by `target_hv / portfolio_hv`. Weights are NOT normalised — scale > 1 means leverage, < 1 means cash residual. Uses `context.config.bars_per_year` for annualisation.
- `BasedOnHV.target_hv` is a decimal (0.15 = 15% vol). No guard against passing integers — spec explicitly calls this a "silent" error. We could add a warning but spec says not to.
- If `portfolio_hv == 0` (all flat prices), return `initial_ratio` unchanged (avoid division by zero).

Files:
- `src/tiportfolio/algos/weigh.py` — Add `Ratio`, `BasedOnHV`
- `tests/test_weigh.py` — Tests for Ratio (normalisation, missing tickers), BasedOnHV (scaling, zero-vol edge case, annualisation)

Steps:
- Implement `Ratio` with normalisation logic
- Implement `BasedOnHV` with volatility computation and scaling
- Write tests with synthetic and controlled-volatility fixtures
