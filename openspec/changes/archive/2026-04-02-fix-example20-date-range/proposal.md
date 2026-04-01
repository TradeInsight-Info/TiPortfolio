## Why

Example 20 (`20_fetch_and_hold.py`) constrains both QQQ and ALLW to start from March 2025 because `fetch_data` is called with a single start date. QQQ has data going back to January 2025, but ALLW only launched in March — so the chart misrepresents QQQ's performance by truncating 2 months. Each portfolio should use its own ticker's natural date range.

Additionally, `data.py` has duplicated normalization logic across `_load_from_csv` and `_split_flat_to_dict` (lowercase columns, timezone handling, sort, dropna) that can be consolidated into a single helper.

## What Changes

- **Example 20 date range**: Change `start="2025-03-05"` → `start="2025-01-02"` so QQQ gets its full date range. ALLW's pre-listing NaN rows are already dropped by `_split_flat_to_dict`'s `dropna(how="all")`. The `Backtest` constructor already subsets data per portfolio.
- **Data normalization consolidation**: Extract a shared `_normalize_ticker_df(df, default_tz)` helper used by both `_load_from_csv` and `_split_flat_to_dict`, eliminating ~10 duplicated lines.

## Capabilities

### New Capabilities
- `data-normalization`: Shared helper for per-ticker DataFrame normalization (lowercase columns, tz → UTC, sort, dropna)

### Modified Capabilities
- `csv-offline-data`: Implementation refactor to use shared normalization helper (no spec-level behavior change)

## Impact

- `src/tiportfolio/data.py` — refactor two functions to use shared helper
- `examples/20_fetch_and_hold.py` — update start date and docstring
- No API changes, no breaking changes
- Existing tests validate behavior; no new tests required
