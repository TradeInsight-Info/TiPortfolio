## Context

The CLI in `cli.py` uses a `shared_options` decorator that applies common flags to all subcommands, and a `_run_backtest()` helper that builds the portfolio and calls `ti.run()`. Adding AIP support means threading a new `--aip` option through this existing plumbing.

## Goals / Non-Goals

**Goals:**
- Add `--aip` option to all CLI subcommands via the shared options decorator
- Route to `ti.run_aip()` when `--aip` is provided, `ti.run()` otherwise
- Works with all existing options (leverage, plot, full, etc.)
- Design the interface so frequency and trigger date can be added later without breaking changes

**Non-Goals (future enhancements):**
- Custom AIP frequency (weekly, quarterly contributions)
- Custom AIP trigger date (e.g. 15th of month instead of month-end)
- Variable contribution amounts over time

## Decisions

### 1. Shared option, not a new subcommand

**Decision**: Add `--aip` to `shared_options` decorator, not create a new `aip` subcommand.

**Rationale**: AIP is orthogonal to Signal choice. A user wants "monthly rebalance with AIP" or "quarterly rebalance with AIP" — it's a modifier, not a strategy. Adding it as a shared option means it works with all existing and future subcommands automatically.

### 2. Implementation in _run_backtest

Add `aip` parameter to `_run_backtest()`. When `aip` is not None and > 0, call `ti.run_aip(..., monthly_aip_amount=aip)` instead of `ti.run(...)`.

```python
# In shared_options:
@click.option("--aip", default=None, type=float, help="Monthly AIP amount (auto investment plan)")

# In _run_backtest:
if aip and aip > 0:
    result = ti.run_aip(*backtests, monthly_aip_amount=aip, leverage=lev)
else:
    result = ti.run(*backtests, leverage=lev)
```

### 3. Leverage + AIP

Both `run_aip()` and `run()` accept the same `leverage` parameter. No special handling needed — just pass `leverage` to whichever function is called.

### 4. Future extensibility design

The CLI and library should be shaped so that future AIP frequency/trigger-date options can be added without breaking existing callers.

**CLI**: `--aip 1000` means monthly-end today. Future flags like `--aip-frequency weekly` and `--aip-day 15` can be added as additional shared options with defaults that preserve current behavior.

**Library**: `run_aip(..., monthly_aip_amount=1000)` is the current API. When we add frequency/trigger-date later, we can either:
- Add optional params: `run_aip(..., monthly_aip_amount=1000, frequency="monthly", day="end")` (backward-compatible)
- Or rename to a more general `aip_amount` with `aip_frequency` — but the `monthly_` prefix in the current param name is intentional documentation of the current behavior.

**For now**: Keep `monthly_aip_amount` as the parameter name. It's honest about what it does. When frequency becomes configurable, we can deprecate it in favor of `aip_amount` + `aip_frequency`.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Adding `aip` kwarg to `_run_backtest` changes its signature | All callers pass `**kwargs` from Click, so `aip` flows through automatically |
| None vs 0.0 ambiguity | Use `default=None` in Click; check `if aip and aip > 0` to be safe |
| `monthly_aip_amount` name locks in frequency | Intentional — honest naming for current behavior; future change adds new params |
