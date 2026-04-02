## Review

### Consistency Check
- All 5 capabilities from proposal are covered by specs: start-of-month-notebook, volatility-targeting-notebook, vix-regime-notebook, dollar-neutral-notebook, beta-neutral-notebook ✓
- API usage is consistent across all specs — all use the same `ti.Portfolio`, `ti.Backtest`, `ti.run()` pattern ✓
- Signal/Select/Weigh/Action algo stack pattern is consistently applied ✓
- Each spec references the correct strategy classes matching `examples/*.py` patterns ✓

### Completeness Check
- All scenarios are testable (each notebook can be executed and outputs verified) ✓
- Data loading strategy is clear: CSV offline for QQQ/BIL/GLD/AAPL/VIX, live fetch only for KVUE ✓
- Multi-backtest comparison is included in every notebook ✓
- Results API coverage is good: summary, full_summary, plot, plot_security_weights, plot_histogram, trades.sample ✓

### Issues Found

1. **`_env.py` path**: Notebooks in `examples/notebooks/` need access to `_env.py` which is in `examples/`. Need to handle the import path (e.g., `sys.path.insert` or inline the CSV mapping). **Decision**: Inline the CSV_DATA dict in a setup cell rather than importing from `_env.py` — notebooks should be self-contained.

2. **Dollar-neutral notebook data**: KVUE (listed Sept 2023) and TXN are not in the CSV cache. The notebook will require network access. This is acceptable and should be noted in the notebook markdown. The date range should be 2023-09-01 to 2024-12-31.

3. **VIX regime notebook**: The `Signal.VIX` API expects `data=vix_data` where `vix_data` is a dict from `ti.fetch_data()`. The spec correctly uses `ti.fetch_data(["^VIX"], csv=CSV_DATA)` ✓

All issues are minor and addressable during implementation. No blocking concerns.
