## Context

`Signal.Schedule` is the single scheduling primitive — all higher-level signals delegate to it. Currently it supports `day="end"` (backward search to last trading day) and `day=int` (forward search to next trading day). The spec mentions `day="start"` but it was never implemented. The parameter `next_trading_day` controls whether non-trading days snap to a valid day.

Key files:
- `src/tiportfolio/algos/signal.py` — Schedule, Monthly, Quarterly, Once classes
- `src/tiportfolio/algo.py` — Or combinator (used by Quarterly)

## Goals / Non-Goals

**Goals:**
- Add `"start"` and `"mid"` day resolution to `Schedule`
- Rename `next_trading_day` → `closest_trading_day` throughout
- Add `Weekly`, `Yearly`, `EveryNPeriods` signal classes
- Update all tests and examples

**Non-Goals:**
- Cron string parsing — decided against (domain mismatch with backtesting)
- Intraday scheduling — engine only supports daily bars
- Engine changes — purely signal-layer additions

## Decisions

### D1: Day resolution search directions

| Day value | Target | Search direction |
|-----------|--------|-----------------|
| `"start"` | Day 1 of period | **Forward** — find first trading day >= day 1 |
| `"mid"` | Midpoint of period (day 15 for months) | **Forward** — find first trading day >= midpoint |
| `"end"` | Last calendar day of period | **Backward** — find last trading day <= last day (existing) |
| `int` (1-31) | That exact day | **Forward** — find first trading day >= target day |

All modes except `"end"` use forward search. This keeps the implementation simple — one search direction for `"start"`, `"mid"`, and `int`, backward only for `"end"`.

**Rationale**: Uniform forward search reduces complexity. `"mid"` users want "around the middle" — landing on the next trading day after the midpoint is close enough and consistent with how `"start"` and `int` work.

### D2: `closest_trading_day` replaces `next_trading_day`

The new name better describes the intent — finding the closest valid trading day. When `closest_trading_day=False`, the signal only fires if the exact target day IS a trading day — no snapping.

This is a breaking change but acceptable because:
- The library is pre-1.0, still in `simplify` branch
- No external users yet
- The rename improves API clarity

### D3: Weekly uses ISO week boundaries

`Signal.Weekly` determines week boundaries using the ISO calendar (Monday = day 1, Sunday = day 7). NYSE trading weeks typically run Mon-Fri.

- `"start"` → first NYSE trading day of the ISO week (usually Monday)
- `"mid"` → first trading day on or after Wednesday
- `"end"` → last NYSE trading day of the ISO week (usually Friday)

Implementation: compare `context.date.isocalendar()` week number with NYSE valid days for that week.

### D4: EveryNPeriods is stateful with period-boundary detection

`EveryNPeriods(n=2, period="week")` fires every 2nd week. It tracks a counter that increments on each period boundary (when the week/month/year number changes from the last evaluation).

```
counter = 0
on each bar:
    if period_changed(current_date, last_date):
        counter += 1
    if counter >= n:
        if is_target_day(current_date, day):  # "start"/"mid"/"end"
            fire, reset counter = 0
```

This is similar to bt's `RunEveryNPeriods` but period-aware (weeks, months) rather than bar-count based.

### D5: `day` resolves at the **period** level for each signal class

The `"start"`, `"mid"`, `"end"` strings mean different target days depending on the signal's period:

| Signal | `"start"` target | `"mid"` target | `"end"` target |
|--------|------------------|----------------|----------------|
| Schedule (monthly) | Day 1 of month | Day 15 of month | Last day of month |
| Weekly | Monday | Wednesday | Friday |
| Quarterly | Day 1 of quarterly month | Day 15 of quarterly month | Last day of quarterly month |
| Yearly | First trading day of Jan | First trading day on/after Jul 1 | Last trading day of Dec |
| EveryNPeriods | First day of period | Midpoint of period | Last day of period |

For **Quarterly**: `day` passes through to `Schedule(month=m, day=day)` for each quarterly month — no special logic needed. `Quarterly(day="start")` fires on the first trading day of Feb, May, Aug, Nov.

For **Yearly**: `day` resolves at year level by mapping to a target month + day:
- `"start"` → `Schedule(month=1, day="start")` → first trading day of January
- `"mid"` → `Schedule(month=7, day="start")` → first trading day on or after July 1
- `"end"` → `Schedule(month=12, day="end")` → last trading day of December
- `int` → treated as month-level day within the configured `month` parameter

**Rationale**: Each signal class interprets `day` at its own period granularity. This is intuitive — `"start"` always means "beginning of this signal's period."

## Risks / Trade-offs

**[Risk] Breaking change from `next_trading_day` rename** → Mitigation: Pre-1.0, no external users. Grep for all usages in tests/examples and update in the same PR.

**[Risk] `"mid"` landing on next week/month** → Mitigation: Forward search from day 15 in a month will always land within the same month (there are always trading days after the 15th). For weekly mid (Wednesday), forward search lands on Wed/Thu/Fri — always same week.

**[Risk] `EveryNPeriods` statefulness across backtests** → Mitigation: Counter resets on each `Backtest.run()` because a fresh `Portfolio` is created. No cross-backtest leakage.
