# CSV Offline Examples & Tests

**Goal**: Migrate examples and e2e tests to use `csv=` parameter with the 6 available CSV tickers (AAPL, QQQ, BIL, GLD, ^VIX, ^VVIX), enabling fully offline runs. Add partial-CSV validation.

**Architecture**: Modify `_load_from_csv` to validate all requested tickers have CSV paths before loading any. Refactor examples to use `csv=` dict with `tests/data/` files. Refactor e2e tests to use `csv=` instead of mocking `_query_yfinance`.

**Tech Stack**: Python 3.12, pandas, tiportfolio

**Spec**: `src/tiportfolio/data.py` (fetch_data with csv parameter)

## File Map

1. Modify: `src/tiportfolio/data.py` — Validate all tickers present in csv dict before loading
2. Modify: `tests/test_data.py` — Add test for partial CSV dict error
3. Modify: `tests/test_e2e.py` — Replace `patch("_query_yfinance")` with `csv=` dict
4. Modify: `examples/01_quick_start.py` through `examples/16_weekly_rebalance.py` — Add `csv=` dict parameter
5. Modify: `examples/11_momentum_top_n.py` — Narrow tickers to available CSVs (QQQ, BIL, GLD, AAPL + 2 others)
6. Modify: `examples/14_dollar_neutral.py` — Narrow tickers to available CSVs

## Chunks

### Chunk A: Partial CSV validation

Add upfront validation in `_load_from_csv`: when `csv` is a dict, check that every ticker has a corresponding key. Raise `FileNotFoundError` listing all missing tickers at once.

Files:
- `src/tiportfolio/data.py`
- `tests/test_data.py`

Steps:
- Add validation at start of `_load_from_csv` when csv is dict
- Add test for partial dict (2 of 3 tickers provided) raises with missing ticker names
- Ensure existing tests still pass

### Chunk B: Migrate examples to csv=

Refactor each example to accept an optional `--offline` flag or always pass `csv=` dict pointing to `tests/data/` files. Examples that use tickers without CSVs (SPY, TLT, EFA, large-caps) need ticker adjustments.

Files:
- All `examples/*.py` files

Steps:
- Define a shared CSV_DATA dict in `examples/_env.py` mapping the 6 tickers to their CSV paths
- Update each example to pass `csv=` when offline CSVs are available
- Adjust examples 03, 04, 08, 09, 11, 14 to use only available CSV tickers

### Chunk C: Migrate e2e tests to csv=

Replace `patch("tiportfolio.data._query_yfinance")` in e2e tests with `csv=` dict pointing to `tests/data/` CSVs.

Files:
- `tests/test_e2e.py`

Steps:
- Build a CSV_PATHS dict in conftest or test_e2e.py
- Replace all `with patch(...)` blocks with `csv=` parameter
