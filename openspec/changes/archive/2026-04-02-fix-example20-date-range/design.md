## Context

`data.py` has two functions that convert raw DataFrames into the standard per-ticker format: `_split_flat_to_dict` (for yfinance/alpaca) and `_load_from_csv` (for offline CSV). Both perform the same 4 steps (lowercase columns → tz normalize → sort → dropna) with only the default timezone differing. Example 20 is constrained to a single start date for both tickers.

## Goals / Non-Goals

**Goals:**
- Allow example 20 to show QQQ from Jan 2025 and ALLW from Mar 2025 on the same chart
- Consolidate duplicated normalization logic into one helper

**Non-Goals:**
- Changing the public `fetch_data` API
- Adding new test files (existing tests cover both paths)
- Modifying `validate_data` or `Backtest` subsetting logic (already correct)

## Decisions

### 1. Extract `_normalize_ticker_df(df, default_tz)` helper

**Choice**: Single private helper that both `_load_from_csv` and `_split_flat_to_dict` call.

**Rationale**: The pattern is identical — the only variable is `default_tz` ("UTC" for CSV, "US/Eastern" for yfinance). A helper with a parameter cleanly captures this.

**Alternative considered**: Leave as-is (only 10 lines duplicated). Rejected because the duplication already caused a consistency bug — `dropna(how="all")` was added to `_split_flat_to_dict` but not `_load_from_csv`. A shared helper prevents this class of divergence.

### 2. Example 20: use `start="2025-01-02"` with single `fetch_data` call

**Choice**: Keep one `fetch_data(["QQQ", "ALLW"], start="2025-01-02")` call. ALLW's pre-listing NaN rows are dropped by the normalization helper. Each `Backtest` subsets data per portfolio.

**Alternative considered**: Two separate `fetch_data` calls merged with `{**qqq_data, **allw_data}`. Rejected — more verbose, and the engine already handles this correctly with one call.

## Risks / Trade-offs

- [Minimal] Adding `dropna(how="all")` to CSV path via shared helper — currently CSV files don't have all-NaN rows, but if they did, this is the correct behavior. Net positive.
- [None] Example date change is purely a constant — no logic risk.
