## Context

TiPortfolio's `run()` function simulates lump-sum investing: portfolio starts with `initial_capital` and no new cash is added. The daily loop in `_run_single()` does: mark-to-market → carry costs → record equity → evaluate algo stack. We need to add a cash injection step into this loop for AIP.

The key code path is in `backtest.py:_run_single()` (lines 292-358). The `_SingleResult` class in `result.py` holds results and computes metrics from the equity curve.

## Goals / Non-Goals

**Goals:**
- Add `run_aip()` that simulates monthly dollar-cost averaging
- Reuse existing engine — minimize code duplication
- Return results compatible with all existing summary/plot methods
- Track contribution metadata (total amount, count)

**Non-Goals:**
- Custom contribution frequencies (weekly, quarterly) — future enhancement
- Variable contribution amounts over time — future enhancement
- Contribution withdrawal / redemption simulation
- Modifying the existing `run()` function behavior

## Decisions

### 1. Separate function vs parameter on `run()`

**Decision**: New `run_aip()` function, not a parameter on `run()`.

**Rationale**: AIP fundamentally changes the simulation semantics (growing capital base). Keeping it separate avoids complicating `run()`'s interface and makes the API self-documenting. Users clearly choose between lump-sum (`run`) and DCA (`run_aip`).

### 2. Cash injection timing

**Decision**: Inject cash on the last trading day of each calendar month, after mark-to-market and carry costs, but before the algo queue evaluates.

**Rationale**: This matches real-world AIP behavior — money arrives, then gets invested at next rebalance. Injecting before the algo queue means if the Signal fires on the same day, the new cash participates immediately. If Signal doesn't fire, cash waits.

**Month-end detection**: Compare current day's month with next trading day's month. If different (or current day is last in the series), it's a month-end.

### 3. Implementation approach — extract helper, not duplicate

**Decision**: Extract the daily loop body from `_run_single()` into a shared helper, then have both `_run_single()` and `_run_single_aip()` call it. Alternatively, add an optional `monthly_aip_amount` parameter to `_run_single()` internally (default `0.0` = no injection) to avoid duplication entirely.

**Chosen**: Add optional `monthly_aip_amount` parameter to `_run_single()`. When `0.0`, behavior is identical to current. This is the simplest change with zero duplication.

```
_run_single(backtest, monthly_aip_amount=0.0) -> _SingleResult
```

### 4. AIP metrics in result

**Decision**: Add optional `total_contributions` and `contribution_count` fields to `_SingleResult.__init__()` with defaults of `0.0` and `0`. Override `summary()` to include them when non-zero.

**Rationale**: Adding optional fields with defaults preserves backward compatibility. Existing `run()` callers see no change.

### 5. Month-end detection algorithm

```python
for i, date in enumerate(trading_days):
    # ... mark-to-market, carry costs, record equity ...

    # AIP injection: last trading day of each month
    if monthly_aip_amount > 0 and i > 0:  # skip first day
        next_date = trading_days[i + 1] if i + 1 < len(trading_days) else None
        if next_date is None or date.month != next_date.month:
            portfolio.cash += monthly_aip_amount
            portfolio.equity += monthly_aip_amount
            contribution_total += monthly_aip_amount
            contribution_count += 1

    # ... evaluate algo queue ...
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Adding params to `_run_single` couples AIP logic into core loop | Default `0.0` means no behavioral change; injection is 5 lines |
| Equity curve includes contributions (not pure investment return) | Document clearly; users can compute pure return via `final_value - total_contributions` |
| Month-end detection depends on sorted trading_days having no gaps | Already guaranteed by existing code — `trading_days = sorted(all_dates)` |
| Parent portfolios with AIP — cash injection at root only | Correct behavior: root gets cash, next rebalance distributes to children via `allocate_equity_to_children` |
