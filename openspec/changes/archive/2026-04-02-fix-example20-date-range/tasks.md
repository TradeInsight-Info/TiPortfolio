> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Extract shared normalization helper

- [x] 1.1 Add `_normalize_ticker_df(df: pd.DataFrame, default_tz: str = "UTC") -> pd.DataFrame` to `src/tiportfolio/data.py` that: lowercases columns, localizes/converts index to UTC, sorts by index, drops all-NaN rows
- [x] 1.2 Refactor `_split_flat_to_dict` to call `_normalize_ticker_df(df, default_tz="US/Eastern")` instead of inline logic
- [x] 1.3 Refactor `_load_from_csv` to call `_normalize_ticker_df(df, default_tz="UTC")` instead of inline logic
- [x] 1.4 Run `uv run pytest tests/ -x -q` — all 248 tests must pass

## 2. Fix example 20 date range

- [x] 2.1 In `examples/20_fetch_and_hold.py`, change `start="2025-03-05"` to `start="2025-01-02"`
- [x] 2.2 Update the docstring to reflect the new date range (Jan 2025 → Apr 2026)
- [x] 2.3 Run example 20 and verify: QQQ chart starts Jan 2025, ALLW chart starts Mar 2025, both display correctly on same figure
