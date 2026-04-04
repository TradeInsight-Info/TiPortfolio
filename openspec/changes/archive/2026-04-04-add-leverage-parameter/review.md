## Review

### Consistency Check
- The proposal lists one new capability: `leverage-parameter` — this is fully covered by `specs/leverage-parameter/spec.md`
- No modified capabilities listed — consistent with the approach of post-simulation scaling (engine untouched)
- Brainstorm chunking aligns with spec requirements: parameter acceptance, return scaling, metadata/naming, tests

### Completeness Check
- All scenarios are testable with existing test infrastructure (fixtures from `conftest.py`)
- Edge cases covered: default leverage, single float broadcast, per-backtest list, length mismatch validation
- Leverage amplifying both gains and losses is specified
- Identity case (leverage=1.0) is explicitly tested

### Issues Found
None — proposal, brainstorm, and specs are consistent. The approach of scaling daily returns post-simulation is well-defined and avoids touching the core engine. All capabilities from the proposal map to spec requirements with testable scenarios.
