## Review

### Consistency Check

The single capability `signal-indicator` from the proposal maps to `specs/signal-indicator/spec.md`. The brainstorm's file map aligns with the proposal impact section.

The spec correctly distinguishes between **state** (SMA50 > SMA200) and **crossing** (state transition from False→True). The `cross` parameter covers up/down/both directions, matching the proposal.

### Completeness Check

- Edge detection logic is fully specified with scenarios for all state pairs (True→True, False→False, True→False, False→True)
- First-bar initialisation is explicitly handled (no spurious fire)
- Insufficient data edge case is specified (pass partial window, let condition decide)
- Composability with `Or(...)` is explicitly tested
- The `ticker` parameter ties the indicator to a specific asset's prices — needed because `context.prices` is a dict of DataFrames

### Issues Found

None. The spec is complete and testable.
