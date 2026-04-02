## Context

The `simplify` branch replaces the old engine-based API (`ScheduleBasedEngine`, `VolatilityBasedEngine`, `FixRatio`, `DollarNeutral`, `BetaScreenerStrategy`) with a new algo-stack pattern (`ti.Portfolio` + `Signal/Select/Weigh/Action`). The 20 example scripts in `examples/` demonstrate the new API for simple cases. We need 5 Jupyter notebooks in `examples/notebooks/` that showcase more complex, real-world strategies — mirroring the master-branch notebooks but using the new API.

## Goals / Non-Goals

**Goals:**
- 5 self-contained Jupyter notebooks demonstrating progressively complex strategies
- Each notebook is executable offline (except dollar-neutral which needs live data for KVUE)
- Consistent structure across all notebooks: setup → strategy → run → explore results → compare
- Cover the full results API (summary, full_summary, plot, plot_security_weights, plot_histogram, trades)
- Educational narrative in markdown cells explaining strategy logic and API usage

**Non-Goals:**
- No changes to `src/tiportfolio/` library code
- No interactive Plotly charts in notebooks (use matplotlib for consistent rendering)
- No Alpaca data source usage (master notebooks used Alpaca; simplify notebooks use YFinance/CSV)
- Not replicating exact parameters from master notebooks — adapt where the new API differs

## Decisions

### 1. Notebook structure: self-contained with inline CSV paths
**Decision**: Each notebook defines its own `CSV_DATA` dict inline rather than importing from `_env.py`.
**Rationale**: Notebooks in `examples/notebooks/` can't import `_env.py` from `examples/` without `sys.path` hacks. Self-contained notebooks are more portable and user-friendly.
**Alternative**: Symlink `_env.py` into `notebooks/` — rejected because it adds maintenance burden.

### 2. Data source: CSV offline by default
**Decision**: Use `ti.fetch_data(tickers, csv=CSV_DATA)` for all notebooks where test CSV data exists (QQQ, BIL, GLD, AAPL, ^VIX). Dollar-neutral notebook uses live `ti.fetch_data()` since TXN/KVUE aren't in CSV cache.
**Rationale**: Offline-first makes notebooks reproducible and CI-friendly.

### 3. Date range: 2019-01-01 to 2024-12-31
**Decision**: Use 2019–2024 for most notebooks (matching existing examples). Dollar-neutral uses 2023-09-01 to 2024-12-31 (KVUE listing date).
**Rationale**: 6 years of data gives meaningful multi-year stats. Consistent with existing `.py` examples.

### 4. Notebook cell structure
**Decision**: Each notebook follows this cell pattern:
1. **Title + description** (markdown) — strategy name, what it demonstrates
2. **Setup** (code) — imports, CSV_DATA, constants
3. **Data loading** (code) — `ti.fetch_data()`
4. **Strategy construction** (code+markdown) — explain algo stack choices
5. **Run + summary** (code) — `ti.run()`, `result.summary()`
6. **Charts** (code) — `result.plot()`, `plot_security_weights()`, `plot_histogram()`
7. **Trade exploration** (code) — `trades.sample()`
8. **Baselines** (code+markdown) — construct baseline strategies
9. **Comparison** (code) — `ti.run(bt1, bt2, bt3)`, `result.summary()`, `result.plot()`

### 5. Complexity progression
**Decision**: Order notebooks from simple to complex:
1. `start_of_month_rebalance` — fixed weights, basic Signal/Weigh
2. `volatility_targeting_qqq_bil_gld` — adaptive weights via BasedOnHV
3. `vix_target_rebalance` — regime switching with parent/child tree
4. `dollar_neutral_txn_kvue` — long/short with parent/child tree
5. `beta_neutral_dynamic` — beta-aware adaptive weights

## Risks / Trade-offs

- **[Risk] Dollar-neutral notebook requires network** → Mitigate by noting this in the notebook markdown and providing expected output in cell outputs
- **[Risk] API may change before merge** → Mitigate by testing each notebook with `uv run` before finalizing
- **[Trade-off] Matplotlib over Plotly** → Simpler rendering in notebook exports, but less interactive. Acceptable for demo purposes since `result.plot(interactive=True)` exists for users who want Plotly.
