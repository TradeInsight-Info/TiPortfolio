## Why

TiPortfolio has 9 example scripts, but 7 of them cover only Chunk 1 basics (equal weight, buy-and-hold, config). Chunks 2–3 delivered major features — branching combinators, momentum selection, volatility targeting, parent/child tree portfolios, VIX regime switching, and short selling — but none have example scripts. New users have no runnable reference for these intermediate and advanced strategies.

## What Changes

- Add 7 new example scripts (`examples/10_*` through `examples/16_*`) covering Chunk 2–3 features
- No source code changes — examples only
- Each script follows the existing pattern: `_env` import, `fetch_data`, portfolio definition, `run`, `summary`, chart save

| Example | Feature Covered | Chunk |
|---------|----------------|-------|
| `10_quarterly_ratio.py` | `Signal.Quarterly` + `Weigh.Ratio` | 2 |
| `11_momentum_top_n.py` | `Select.Momentum` | 2 |
| `12_branching_skip_december.py` | `And`/`Not` combinators | 2 |
| `13_volatility_targeting.py` | `Weigh.BasedOnHV` | 2 |
| `14_dollar_neutral.py` | Parent/child tree + `Weigh.Equally(short=True)` | 3 |
| `15_vix_regime_switching.py` | `Signal.VIX` + child portfolios | 3 |
| `16_weekly_rebalance.py` | `Signal.Weekly` | 2 |

## Capabilities

### New Capabilities

- `example-scripts-chunk-2-3`: Runnable example scripts demonstrating all Chunk 2–3 features

### Modified Capabilities

_(none — no existing spec requirements change)_

## Impact

- **Code**: No source changes
- **Examples**: 7 new files in `examples/`
- **Dependencies**: None
- **Risk**: Zero — additive only, no existing behavior affected
