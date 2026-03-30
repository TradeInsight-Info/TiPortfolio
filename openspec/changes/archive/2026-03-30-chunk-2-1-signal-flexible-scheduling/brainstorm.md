# Signal Flexible Scheduling

**Goal**: Expand `Signal.Schedule` with `"start"`/`"mid"` day aliases, rename `next_trading_day` → `closest_trading_day`, and add `Signal.Weekly`, `Signal.Yearly`, `Signal.EveryNPeriods` for flexible frequency-based scheduling.

**Architecture**: Extend existing `Signal.Schedule` primitive with new day resolution modes. Add new `Algo` subclasses that delegate to `Schedule` (same composition pattern as `Monthly`/`Quarterly`). `EveryNPeriods` is stateful (tracks period boundaries across bars).

**Tech Stack**: Python 3.12, pandas, pandas-market-calendars (NYSE calendar)

**Spec**: `docs/superpowers/specs/2026-03-28-core-engine-implementation-design.md` Section 5 (algo catalogue)

## File Map

1. Modify: `src/tiportfolio/algos/signal.py` — Add `"start"`/`"mid"` day resolution, rename `next_trading_day` → `closest_trading_day`, add `Weekly`, `Yearly`, `EveryNPeriods`
2. Modify: `tests/test_signal.py` — Update existing tests for param rename, add tests for new day modes and new signal classes
3. Modify: `tests/test_e2e.py` — Verify new signal classes are accessible
4. Modify: `examples/` — Update any examples using `next_trading_day` param

## Chunks

### Chunk 1: Schedule Day Expansion + Param Rename

Expand `Signal.Schedule` day parameter to accept `"start"` | `"mid"` | `"end"` | int(1-31). Rename `next_trading_day` → `closest_trading_day`.

**Day resolution rules:**
- `"start"` → Target day 1 of month. Search **forward** to next trading day.
- `"mid"` → Target middle day of month (day 15 or midpoint). Search **forward** to next trading day (same direction as `"start"` and `int`).
- `"end"` → Target last calendar day. Search **backward** to last trading day. (Existing behavior, unchanged.)
- `int` (1-31) → Target that day. When `closest_trading_day=True` (default), search **forward** to next trading day. When `False`, no signal fires if not a trading day.

**Param rename:** `next_trading_day` → `closest_trading_day` (same default `True`). The new name better reflects the `"mid"` bidirectional behavior. This is a **breaking change** for anyone using the keyword argument explicitly.

Files:
- `src/tiportfolio/algos/signal.py`
- `tests/test_signal.py`

Steps:
- Rename `next_trading_day` → `closest_trading_day` in `Schedule.__init__`
- Add `_is_first_trading_day_of_month` for `"start"` (forward search)
- Add `_matches_mid_day` for `"mid"` (forward search from day 15)
- Update `_matches_int_day` to use `closest_trading_day` param name
- Update existing tests that reference `next_trading_day`
- Add tests for `"start"` and `"mid"` modes

### Chunk 2: New Signal Classes (Weekly, Yearly, EveryNPeriods)

Add three new `Algo` subclasses to the `Signal` namespace.

**Signal.Weekly(day="end"):**
- `"end"` → last trading day of the week (typically Friday)
- `"start"` → first trading day of the week (typically Monday)
- `"mid"` → first trading day on or after Wednesday
- Delegates to per-week calendar logic using NYSE calendar

**Signal.Yearly(day="end"):**
- `day` resolves at **year** level, not month level:
  - `"start"` → first trading day of the year (January)
  - `"mid"` → first trading day on or after July 1 (mid-year)
  - `"end"` → last trading day of the year (December) — default
- Uses `Or(Schedule(month=target_month, day=target_day))` internally

**Signal.EveryNPeriods(n, period, day="end"):**
- `period`: `"day"` | `"week"` | `"month"` | `"year"`
- `n`: fire every N periods
- `day`: `"start"` | `"mid"` | `"end"` — which day within the period to fire on
- Stateful: tracks period boundaries using a counter, fires when the N-th period boundary is crossed
- Example: `EveryNPeriods(n=2, period="week", day="end")` = biweekly on last trading day of the target week

Files:
- `src/tiportfolio/algos/signal.py`
- `tests/test_signal.py`
- `tests/test_e2e.py`

Steps:
- Implement `Weekly` with NYSE week-boundary detection
- Implement `Yearly` as thin delegate to `Schedule`
- Implement `EveryNPeriods` with stateful period tracking
- Add tests for each: Weekly fires once/week, Yearly fires once/year, EveryNPeriods fires every N periods
- Update e2e import checks

### Chunk 3: Quarterly/Yearly Day Semantics + Param Rename Propagation

Update `Quarterly` and `Yearly` so `day` resolves at the **period** level (not just month level). Propagate `closest_trading_day` rename.

**Signal.Quarterly day resolution:**
Currently `Quarterly(months=[2,5,8,11], day="end")` creates `Or(Schedule(month=m, day="end") for m)`. With the new day modes:
- `day="end"` → last trading day of each quarterly month (existing, unchanged)
- `day="start"` → first trading day of each quarterly month
- `day="mid"` → mid-month (day 15) of each quarterly month, forward search
- `day=int` → that day within each quarterly month

This already works via Schedule pass-through — no Quarterly logic change needed for day, just the param rename.

**Signal.Yearly day resolution:**
`day` resolves at **year** level:
- `"start"` → first trading day of January
- `"mid"` → first trading day on or after July 1
- `"end"` → last trading day of December (default)

Files:
- `src/tiportfolio/algos/signal.py` (Monthly/Quarterly/Yearly constructors)
- `examples/*.py` (if any use `next_trading_day`)

Steps:
- Update `Monthly.__init__` signature: `next_trading_day` → `closest_trading_day`
- Implement `Yearly` with year-level day semantics (start=Jan, mid=Jul, end=Dec)
- Add tests for Quarterly with `day="start"` and `day="mid"`
- Add tests for Yearly with `day="start"` and `day="mid"`
- Grep examples for `next_trading_day` and update
