## Why

Examples and e2e tests hit YFinance on every run, making them non-reproducible and unusable offline. We already have CSV files in `tests/data/` for 6 tickers (AAPL, QQQ, BIL, GLD, ^VIX, ^VVIX) and just added a `csv=` parameter to `fetch_data`. We need to wire them together — and add validation so that passing a partial CSV dict (missing tickers) gives a clear error instead of a cryptic `KeyError`.

## What Changes

- **Partial CSV validation**: When `csv=` is a dict, validate all requested tickers have entries before loading. Raise `FileNotFoundError` listing all missing tickers.
- **Examples migration**: All 16 example scripts pass `csv=` dict pointing to `tests/data/` CSVs. Examples using tickers without CSVs (SPY, TLT, EFA, large-caps) get narrowed to available tickers.
- **E2E test migration**: Replace `patch("tiportfolio.data._query_yfinance")` mocking with `csv=` parameter, using real CSV fixture data.

## Capabilities

### New Capabilities

- `csv-offline-data`: Partial-CSV validation in `fetch_data(csv=dict)` and offline-first example/test patterns

### Modified Capabilities

_(none)_

## Impact

- **Code**: `src/tiportfolio/data.py` — 5-line validation addition
- **Tests**: `tests/test_data.py` (1 new test), `tests/test_e2e.py` (replace mocks with csv=)
- **Examples**: All 16 scripts updated to add `csv=` parameter
- **Risk**: Low — additive validation; examples gain offline mode without removing network mode
