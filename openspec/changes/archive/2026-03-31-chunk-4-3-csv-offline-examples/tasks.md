> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Partial CSV Validation (both modes)

- [x] 1.1 Add upfront validation in `_load_from_csv` for dict mode: check `set(tickers) - set(csv.keys())`, raise `FileNotFoundError` listing all missing tickers
- [x] 1.2 Refactor directory mode in `_load_from_csv` to collect all missing tickers first, then raise a single `FileNotFoundError` listing them all (instead of raising on first miss)
- [x] 1.3 Add tests in `tests/test_data.py`: partial csv dict raises with missing ticker names; partial csv directory raises with missing ticker names
- [x] 1.4 Run `tests/test_data.py` to verify all pass

## 2. Shared CSV Helper

- [x] 2.1 Add `CSV_DATA` dict in `examples/_env.py` mapping the 6 available tickers to `tests/data/*_2018_2024_yf.csv` paths

## 3. Migrate Examples to csv=

- [x] 3.1 Update example 01 (Quick Start): add `csv=` parameter AND add docstring/comments explaining csv= enables offline/faster testing, without csv= requires network
- [x] 3.2 Update examples 02, 05, 06, 07, 10, 12, 13, 16 — add `csv=` parameter (tickers already match available CSVs)
- [x] 3.3 Update example 03 (two asset): change SPY,TLT → QQQ,BIL; add `csv=`
- [x] 3.4 Update example 04 (single asset): change SPY → QQQ; add `csv=`
- [x] 3.5 Update example 08 (beta neutral): change SPY benchmark → AAPL; add `csv=`
- [x] 3.6 Update example 09 (ERC): change SPY,TLT,GLD,BIL → QQQ,AAPL,GLD,BIL; add `csv=`
- [x] 3.7 Update example 11 (momentum): narrow to QQQ,AAPL,BIL,GLD; add `csv=`
- [x] 3.8 Update example 14 (dollar neutral): narrow to QQQ,AAPL,BIL,GLD; add `csv=`
- [x] 3.9 Update example 15 (VIX regime): add `csv=` for both data and vix_data calls

## 4. Migrate E2E Tests

- [x] 4.1 Replace all `patch("tiportfolio.data._query_yfinance")` in `tests/test_e2e.py` with `csv=` dict using `tests/data/*_yf.csv` CSVs
- [x] 4.2 Run full test suite to verify no regressions
