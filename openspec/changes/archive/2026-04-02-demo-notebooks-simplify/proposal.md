## Why

The `simplify` branch introduces a completely new API (Portfolio + Algo Stack pattern) replacing the old engine-based design. The 6 master-branch notebooks are the primary user-facing documentation for portfolio strategies, but they use the old API (`ScheduleBasedEngine`, `VolatilityBasedEngine`, `FixRatio`, `DollarNeutral`, etc.). We need equivalent notebooks demonstrating the same 5 strategies (excluding `data_preparation`) with the new `ti.Portfolio`, `ti.Signal.*`, `ti.Weigh.*`, `ti.run()` API to serve as demos for the simplified design.

## What Changes

- Create 5 new Jupyter notebooks in `examples/notebooks/`
- Each notebook mirrors a master-branch notebook but uses the new simplified API
- Notebooks progress from simple → complex: fixed ratio → vol targeting → VIX regime → dollar-neutral → beta-neutral
- All use offline CSV data where possible for reproducibility; live fetch for tickers not in CSV cache (KVUE)
- Demonstrate the full results API: `summary()`, `full_summary()`, `plot()`, `plot_security_weights()`, `trades.sample()`, `plot_histogram()`
- Multi-backtest comparison via `ti.run(bt1, bt2, bt3)` in every notebook

## Capabilities

### New Capabilities
- `start-of-month-notebook`: Fixed 70/20/10 monthly rebalance using `Weigh.Ratio` + `Signal.Monthly`
- `volatility-targeting-notebook`: Inverse-vol weighting using `Weigh.BasedOnHV` with quarterly schedule
- `vix-regime-notebook`: VIX regime switching using `Signal.VIX` + parent/child portfolio tree
- `dollar-neutral-notebook`: Long/short pair trade (TXN/KVUE) using parent/child tree with `Weigh.Equally(short=True)`
- `beta-neutral-notebook`: Beta-neutral strategy using `Weigh.BasedOnBeta(target_beta=0)` with broader universe

### Modified Capabilities

_(none — these are new notebooks, no existing specs are modified)_

## Impact

- **New files**: 5 `.ipynb` files in `examples/notebooks/`
- **Dependencies**: Uses existing `_env.py` CSV_DATA pattern; may need symlink or copy for notebook directory
- **No code changes**: Pure documentation/demo work — no changes to `src/tiportfolio/`
