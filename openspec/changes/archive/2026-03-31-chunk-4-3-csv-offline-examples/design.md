## Context

`fetch_data` gained a `csv=` parameter in the previous session. Currently `_load_from_csv` handles dict and directory modes, but missing tickers cause errors deep in the loading loop — not user-friendly. Examples still hit YFinance.

Available CSV files in `tests/data/`: `aapl`, `qqq`, `bil`, `gld`, `vix`, `vvix` (all `*_2018_2024_yf.csv`).

## Goals / Non-Goals

**Goals:**
- Validate csv upfront for **both** dict and directory modes with helpful error listing all missing tickers
- All examples pass `csv=` dict to run offline with `tests/data/` CSVs
- Quick Start example documents the `csv=` parameter for new users
- E2e tests use `csv=` instead of mocking internals
- A shared helper in `examples/_env.py` provides the CSV paths mapping

**Non-Goals:**
- Not adding new CSV files for missing tickers (SPY, TLT, EFA, etc.)
- Not adding `--offline` CLI flag — just hardcode CSV paths in examples
- Not changing conftest synthetic fixtures (those are for unit tests)

## Decisions

### 1. Validation in `_load_from_csv` for both modes

**Dict mode**: Check `set(tickers) - set(csv.keys())` upfront. Collect all missing tickers, then raise `FileNotFoundError` listing them all in one message.

**Directory mode**: The existing loop already discovers files per-ticker, but currently raises on the first miss. Refactor to collect ALL missing tickers first, then raise a single error listing them all. This way users see all gaps at once rather than fixing them one at a time.

### 2. Shared CSV_DATA dict in `examples/_env.py` using `_yf.csv` suffix

Add a `CSV_DATA` dict in `_env.py` mapping tickers to their YFinance-sourced CSV paths (the `*_2018_2024_yf.csv` files). Examples import it and pass as `csv=CSV_DATA`. The `_yf.csv` suffix is important — these are the YFinance-compatible format with `date,open,high,low,close,volume` columns and UTC timestamps.

```python
CSV_DATA = {
    "AAPL": "tests/data/aapl_2018_2024_yf.csv",
    "QQQ": "tests/data/qqq_2018_2024_yf.csv",
    "BIL": "tests/data/bil_2018_2024_yf.csv",
    "GLD": "tests/data/gld_2018_2024_yf.csv",
    "^VIX": "tests/data/vix_2018_2024_yf.csv",
    "^VVIX": "tests/data/vvix_2018_2024_yf.csv",
}
```

### 3. Quick Start documentation

Add a comment block in `examples/01_quick_start.py` explaining:
- `csv=` enables faster offline testing with local CSV files
- Without `csv=`, network access is required to download ticker data
- Users can remove `csv=` to fetch live data

### 4. Example ticker adjustments

| Example | Current tickers | Adjusted tickers |
|---------|----------------|-----------------|
| 03 (two asset) | SPY, TLT | QQQ, BIL |
| 04 (single asset) | SPY | QQQ |
| 08 (beta neutral) | QQQ,BIL,GLD + SPY benchmark | QQQ,BIL,GLD + AAPL benchmark |
| 09 (ERC) | SPY,TLT,GLD,BIL | QQQ,AAPL,GLD,BIL |
| 11 (momentum) | QQQ,SPY,TLT,GLD,BIL,EFA | QQQ,AAPL,BIL,GLD |
| 14 (dollar neutral) | 10 large-caps | QQQ,AAPL,BIL,GLD |

### 5. E2E tests: csv= instead of patch

Build a `CSV_PATHS` dict in test_e2e.py pointing to `tests/data/*_yf.csv` files. Replace all `with patch(...)` + `ti.fetch_data(...)` blocks with direct `ti.fetch_data(..., csv=CSV_PATHS)`.

## Risks / Trade-offs

- **[Ticker reduction in examples]** → Some examples become less realistic (4 tickers instead of 10). Acceptable for offline testing; users can remove `csv=` param to use real data.
- **[Directory mode validation change]** → Currently raises on first missing ticker; new behavior collects all. This is more user-friendly but changes error messages slightly.
