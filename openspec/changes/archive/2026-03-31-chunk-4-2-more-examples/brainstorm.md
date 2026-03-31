# Chunk 4.2: More Examples (Chunks 2–4 Coverage)

**Goal**: Fill the example gap — chunks 2, 3, and 4 introduced major features (branching, momentum, volatility targeting, tree portfolios, VIX regime switching, short selling) but only chunks 1 and 4 have example scripts.

**Architecture**: Pure example scripts in `examples/`. No source code changes. Each script is standalone, follows the existing pattern (import `_env`, fetch data, build portfolio, run, print summary, save chart).

**Tech Stack**: Python 3.12, tiportfolio

**Spec**: `docs/work-plan/chunk-2-algos-branching.md`, `docs/work-plan/chunk-3-trees-shorts.md`, `docs/guides/allocation-strategies.md`

## File Map

1. Create: `examples/10_quarterly_ratio.py` — Quarterly rebalance with fixed ratio weights
2. Create: `examples/11_momentum_top_n.py` — Momentum-based top-N selection
3. Create: `examples/12_branching_skip_december.py` — And/Not combinators to skip months
4. Create: `examples/13_volatility_targeting.py` — BasedOnHV volatility targeting
5. Create: `examples/14_dollar_neutral.py` — Parent/child tree, long+short legs
6. Create: `examples/15_vix_regime_switching.py` — VIX signal with child portfolio switching
7. Create: `examples/16_weekly_rebalance.py` — Weekly signal scheduling

## Chunks

### Chunk A: Chunk 2 Examples (Algos + Branching)

Scripts covering the features delivered in Chunk 2: quarterly scheduling, momentum selection, branching combinators, ratio weighting, and volatility targeting.

Files:
- `examples/10_quarterly_ratio.py`
- `examples/11_momentum_top_n.py`
- `examples/12_branching_skip_december.py`
- `examples/13_volatility_targeting.py`
- `examples/16_weekly_rebalance.py`

Steps:
- Write each example following the existing pattern (01–09)
- Each script demonstrates one primary feature with clear docstring explaining the strategy

### Chunk B: Chunk 3 Examples (Trees + Short Selling)

Scripts covering parent/child tree portfolios, dollar-neutral strategies, and VIX regime switching.

Files:
- `examples/14_dollar_neutral.py`
- `examples/15_vix_regime_switching.py`

Steps:
- Write dollar-neutral using parent with long+short children and Select.Momentum
- Write VIX regime switching using Signal.VIX with two child portfolios
