## Context

TiPortfolio's Chunk 1 delivered a working leaf-only backtest engine with `AlgoQueue` → `Context` pipeline. All algos are `Algo` subclasses implementing `__call__(context: Context) -> bool`. The algo stack flows: Signal → Select → Weigh → Action. Chunk 2 adds 8 new algo classes and 3 combinators without modifying the engine.

Current state:
- `algo.py`: `Context`, `Algo` ABC, `AlgoQueue` — stable, well-tested
- `algos/signal.py`: `Schedule` (day="end" only), `Monthly`, `Once`
- `algos/select.py`: `Select.All` only
- `algos/weigh.py`: `Weigh.Equally` only (with `short=True` support)
- `algos/rebalance.py`: `Action.Rebalance`, `Action.PrintInfo` — unchanged in this chunk

Spec authority: `docs/superpowers/specs/2026-03-28-core-engine-implementation-design.md` Sections 2 and 5.

## Goals / Non-Goals

**Goals:**
- Implement `Or`, `And`, `Not` combinators in `algo.py`
- Complete `Signal.Schedule(day=int)` with NYSE calendar resolution
- Add `Signal.Quarterly` composing `Or` + `Schedule`
- Add `Select.Momentum` (lookback return ranking) and `Select.Filter` (boolean gate)
- Add `Weigh.Ratio` (explicit weights, normalised) and `Weigh.BasedOnHV` (volatility scaling)
- Export `Or`, `And`, `Not` at `ti.*` level
- 80%+ test coverage for all new code

**Non-Goals:**
- Engine changes (`backtest.py`) — no modifications
- Parent/child portfolio support — Chunk 3
- `Signal.VIX` — Chunk 3
- `Weigh.BasedOnBeta`, `Weigh.ERC` — Chunk 4
- Results/charting changes — Chunk 5
- Performance optimisation (no caching of calendar lookups, etc.)

## Decisions

### D1: Combinators live in `algo.py`, not a separate file

**Choice**: Add `Or`, `And`, `Not` directly to `algo.py` alongside `AlgoQueue`.

**Rationale**: They are core abstractions at the same level as `AlgoQueue` — `And` is literally a nestable `AlgoQueue`. A separate `branching.py` file for 3 small classes (~30 lines total) would fragment related concepts. The spec mentions `branching.py` as a re-export point but the actual classes are defined in `algo.py`.

**Alternative considered**: Separate `branching.py` — rejected because it splits tightly coupled abstractions across files for no benefit.

### D2: `Or` uses `any()` with short-circuit, side effects are intentional

**Choice**: `Or.__call__` uses `any(algo(context) for algo in self._algos)` — stops on first `True`.

**Rationale**: Spec defines `Or` as "returns True when any inner algo returns True (short-circuits on first True)." This means algos after the first `True` do NOT execute, and their context mutations don't happen. This is correct and intentional — `Or` is a signal combinator, not a "run all and merge" operator. Users who want all side effects should use explicit sequencing.

### D3: `Schedule(day=int)` snaps forward using NYSE calendar

**Choice**: When `day=15` falls on a non-trading day, find the next valid NYSE trading day in the same month. If no valid day exists after the target day in that month, no signal fires.

**Rationale**: `next_trading_day=True` (default) is the practical choice — users expect "rebalance around the 15th" not "skip months where the 15th is a Saturday." Setting `next_trading_day=False` gives strict behavior for users who want it.

**Implementation**: Query NYSE calendar for valid days in the month, find first day >= target day.

### D4: `Momentum` operates only on string tickers, not Portfolio children

**Choice**: `Select.Momentum` filters `context.selected` to keep only `str` items, ignoring `Portfolio` objects.

**Rationale**: Spec states "only operates on ticker strings." Momentum ranking needs price history which only exists for tickers, not sub-portfolios. Parent-level momentum selection is out of scope.

### D5: `Filter` returns False to halt queue, does NOT modify `context.selected`

**Choice**: `Filter.__call__` returns the boolean result of `condition(row)` without touching `context.selected`.

**Rationale**: This is a gate, not a selector. A `False` return short-circuits `AlgoQueue`, so no rebalance happens and positions hold from the previous period. This is the spec-defined behavior and is the most useful pattern for regime filtering.

### D6: `Ratio` normalises to `sum(|w|) = 1.0`

**Choice**: Always fully invested. Weights are divided by sum of absolute values.

**Rationale**: Spec-defined. Prevents users from accidentally over/under-investing. Tickers in `selected` but missing from the `weights` dict get weight 0 (position closed on rebalance).

### D7: `BasedOnHV` uses diagonal covariance approximation

**Choice**: Portfolio HV = `sqrt(sum((w * hv)^2))` — ignores cross-asset correlation.

**Rationale**: Spec-defined. Simpler than full covariance matrix, and the approximation is reasonable for vol-targeting where the exact portfolio vol matters less than the scaling direction. Full covariance is reserved for `Weigh.ERC` in Chunk 4.

## Risks / Trade-offs

**[Risk] `Schedule(day=int)` edge case: month with no trading days after target day** → Mitigation: Return `False` (no signal). Document that day=31 only fires in months with 31+ calendar days that have trading activity on or after the 31st.

**[Risk] `BasedOnHV` silent misuse with integer `target_hv`** → Mitigation: Spec explicitly says no guard. This is a known footgun. Could add a `UserWarning` if `target_hv > 1.0` but spec says not to. Follow spec.

**[Risk] `Momentum` lookback window exceeds available data** → Mitigation: If `start` is before the earliest date in `context.prices[ticker]`, pandas `.loc[start:end]` gracefully returns the available subset. `pct_change().sum()` on insufficient data produces a smaller sum, which is a natural penalty for newer tickers.

**[Trade-off] No caching of NYSE calendar lookups in `Schedule`** → Accepted for now. Calendar lookups are called once per bar per signal algo — with ~252 bars/year and microsecond-level lookups, performance is not a concern. Optimise in a future chunk if profiling shows it matters.
