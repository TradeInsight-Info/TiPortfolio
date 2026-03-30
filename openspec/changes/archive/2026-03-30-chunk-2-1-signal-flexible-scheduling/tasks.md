> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [x]) syntax for tracking.

## 1. Schedule Day Expansion + Param Rename

- [x] 1.1 Rename `next_trading_day` → `closest_trading_day` in `Signal.Schedule.__init__` and all internal references in `signal.py`
- [x] 1.2 Rename `next_trading_day` → `closest_trading_day` in `Signal.Monthly.__init__`
- [x] 1.3 Implement `day="start"` in `Signal.Schedule` — forward search from day 1 to first NYSE trading day of month
- [x] 1.4 Implement `day="mid"` in `Signal.Schedule` — forward search from day 15 to first NYSE trading day on or after
- [x] 1.5 Update existing tests in `test_signal.py` — replace all `next_trading_day` references with `closest_trading_day`
- [x] 1.6 Add tests for `day="start"`: first-day-is-trading-day, first-day-is-weekend, month filter
- [x] 1.7 Add tests for `day="mid"`: mid-is-trading-day, mid-is-saturday (forward to Monday), mid-is-sunday (forward to Monday), strict mode
- [x] 1.8 Run tests — all pass

## 2. Signal.Weekly

- [x] 2.1 Implement `Signal.Weekly` in `signal.py` — fires once per ISO week using NYSE calendar, accepts `day` (`"start"` | `"mid"` | `"end"`) and `closest_trading_day`
- [x] 2.2 Add tests: default end-of-week fires ~4-5 times per month, start-of-week fires on Monday, mid-week on/after Wednesday, short week with holiday
- [x] 2.3 Run tests — all pass

## 3. Signal.Yearly (year-level day resolution)

- [x] 3.1 Implement `Signal.Yearly` in `signal.py` — day resolves at year level: `"start"` → Jan, `"mid"` → Jul, `"end"` → Dec. Optional `month` param for overrides.
- [x] 3.2 Add tests: default fires last trading day of Dec, `day="start"` fires first trading day of Jan, `day="mid"` fires on/after Jul 1, custom `month` override
- [x] 3.3 Run tests — all pass

## 4. Signal.Quarterly (default months change + day modes)

- [x] 4.1 Change `Quarterly` default months from `[2, 5, 8, 11]` to `[1, 4, 7, 10]` (calendar quarters) in `signal.py`
- [x] 4.2 Update existing Quarterly tests to expect `{1, 4, 7, 10}` instead of `{2, 5, 8, 11}`
- [x] 4.3 Add tests for `Quarterly(day="start")` — fires on first trading day of Jan, Apr, Jul, Oct
- [x] 4.4 Add tests for `Quarterly(day="mid")` — fires on first trading day on/after 15th of Jan, Apr, Jul, Oct
- [x] 4.5 Add tests for `Quarterly(day=int)` — fires on that day in Jan, Apr, Jul, Oct
- [x] 4.6 Run tests — all pass

## 5. Signal.EveryNPeriods

- [x] 5.1 Implement `Signal.EveryNPeriods` in `signal.py` — stateful counter with period boundary detection for `"day"` | `"week"` | `"month"` | `"year"`, accepts `day` param for within-period targeting
- [x] 5.2 Add tests: biweekly fires every 2 weeks, every-3-months fires 4x per year, every-2-days fires on alternating days, day param controls which day in period, first period fires immediately
- [x] 5.3 Run tests — all pass

## 6. Integration + Examples

- [x] 6.1 Update `tests/test_e2e.py` — verify `Signal.Weekly`, `Signal.Yearly`, `Signal.EveryNPeriods` are accessible
- [x] 6.2 Grep examples for `next_trading_day` and update to `closest_trading_day`
- [x] 6.3 Run full test suite — all existing + new tests pass
