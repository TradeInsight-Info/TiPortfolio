## Context

Chunk 1 is complete with 91 tests passing. Two refinements needed before moving to Chunk 2.

## Goals / Non-Goals

**Goals:**
- Single source of truth for fees: TiConfig only
- Buy-and-hold expressible as `Signal.Once()` in the algo stack

**Non-Goals:**
- Any Chunk 2+ features

## Decisions

### Signal.Once uses instance state `_fired` flag
**Decision:** `Signal.Once` stores `self._fired = False` and flips to `True` after the first call.

**Why:** Simplest possible implementation. The same pattern as Signal.VIX's `_active` lazy state. No need for date tracking or external state.

**Trade-off:** Like Signal.VIX, `_fired` persists across `ti.run()` calls if the same Portfolio object is reused. This is acceptable — same limitation, same future fix (Chunk 3+ can add a reset mechanism).

### Backtest constructor becomes simpler
**Decision:** Remove `fee_per_share` entirely. The `replace()` call on frozen TiConfig is no longer needed in Backtest.

## Risks / Trade-offs

- **[Risk] Breaking change** → Low risk — Chunk 1 is not released, only internal usage. Update the one example and test that use it.
