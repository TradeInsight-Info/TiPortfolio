## Why

Users need a simple way to compare strategies at different leverage levels without manually scaling weights. Currently, leverage only happens implicitly when algo-generated weights exceed 1.0 — there's no clean API to say "show me this portfolio at 2x leverage" for comparison or analysis.

## What Changes

- Add a `leverage` keyword argument to `run()` that accepts `float | list[float]`, defaulting to `1.0`
- When leverage != 1.0, scale the equity curve's daily returns by the leverage factor, rebuilding a synthetic leveraged equity curve
- Store leverage metadata in results so summaries display the applied leverage factor
- Append leverage suffix to portfolio names (e.g., "MyPortfolio (2.0x)") for clear identification in multi-backtest comparisons

## Capabilities

### New Capabilities
- `leverage-parameter`: Accept leverage multiplier in `run()`, apply to equity curves, and reflect in result metadata/naming

### Modified Capabilities
<!-- No existing spec-level requirements change. The engine simulation is untouched — leverage is applied post-simulation. -->

## Impact

- **Code**: `src/tiportfolio/backtest.py` (run signature + leverage application), `src/tiportfolio/result.py` (metadata storage + display)
- **API**: `run()` gains a new keyword-only argument — fully backward compatible (default=1.0)
- **Dependencies**: None — uses only pandas operations already in use
