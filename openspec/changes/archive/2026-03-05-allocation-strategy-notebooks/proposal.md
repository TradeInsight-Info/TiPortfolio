## Why

The three new allocation strategies (VolatilityTargeting, DollarNeutral, BetaNeutral) have no demonstration notebooks, making them hard to evaluate or use. DollarNeutral also lacks asymmetric book sizing, blocking real pairs-trading ratios like 1:1.135.

## What Changes

- **`DollarNeutral` enhancement**: add `long_book_size` / `short_book_size` params so each leg can be sized independently (e.g., long 46.8% TXN, short 53.2% KVUE for a 1:1.135 hedge ratio)
- **Beta screener utility** (`notebooks/utils/beta_screener.py`): given a YFinance universe and a lookback window, returns the N highest-beta and N lowest-beta symbols ranked at a given date — used by the BetaNeutral notebook to select the long/short book each month
- **Notebook: DollarNeutral TXN/KVUE** (`notebooks/dollar_neutral_txn_kvue.ipynb`): long TXN / short KVUE at 1:1.135 ratio, monthly mid-month rebalance via `ScheduleBasedEngine`, compared to long-TXN-only and short-KVUE-only
- **Notebook: VolatilityTargeting QQQ/BIL/GLD** (`notebooks/volatility_targeting_qqq_bil_gld.ipynb`): inverse-vol weighted QQQ/BIL/GLD (baseline 70/20/10), monthly mid-month rebalance, compared to fixed-weight and long-QQQ; optional target_vol parameter
- **Notebook: BetaNeutral dynamic** (`notebooks/beta_neutral_dynamic.ipynb`): each month screener ranks a 30-stock universe by rolling beta vs SPY, goes long the 5 lowest-beta stocks and short the 5 highest-beta stocks with weights sized for zero net portfolio beta, monthly mid-month rebalance, compared to long SPY

## Capabilities

### New Capabilities
- `dollar-neutral-notebook`: demonstration and comparison notebook for DollarNeutral pairs trading
- `volatility-targeting-notebook`: demonstration and comparison notebook for VolatilityTargeting
- `beta-neutral-notebook`: dynamic beta-ranked long/short notebook using BetaNeutral + screener
- `beta-screener-util`: utility that ranks a stock universe by rolling OLS beta at a given date

### Modified Capabilities
- `dollar-neutral`: asymmetric `long_book_size` / `short_book_size` params (backward-compatible)

## Impact

- `src/tiportfolio/allocation.py`: `DollarNeutral` gets `long_book_size` / `short_book_size` fields
- `tests/test_allocation_dollar_neutral.py`: new tests for asymmetric sizing
- `notebooks/dollar_neutral_txn_kvue.ipynb`: new
- `notebooks/volatility_targeting_qqq_bil_gld.ipynb`: new
- `notebooks/beta_neutral_dynamic.ipynb`: new
- `notebooks/utils/beta_screener.py`: new utility module
- Dependencies: `yfinance` (already in project), no new packages required
