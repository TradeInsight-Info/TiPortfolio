## ADDED Requirements

### Requirement: DollarNeutral notebook demonstrates TXN/KVUE pairs trade

`notebooks/dollar_neutral_txn_kvue.ipynb` SHALL demonstrate the `DollarNeutral` strategy with TXN long and KVUE short at a 1:1.135 hedge ratio, using `ScheduleBasedEngine` with `Schedule("month_mid")` and data from YFinance.

Notebook sections (in order):
1. Setup — imports, cache, constants (`LONG="TXN"`, `SHORT="KVUE"`, `CASH="BIL"`, `START`, `END`, `RATIO=1.135`)
2. Data — fetch TXN, KVUE, BIL via YFinance; show shape
3. Strategy — construct `DollarNeutral` with `long_book_size = 1/(1+RATIO)`, `short_book_size = RATIO/(1+RATIO)`, `Schedule("month_mid")`
4. Run backtest — print `result.summary()`
5. Portfolio chart — `plot_portfolio_with_assets_interactive` with rebalances marked
6. Rebalance table — `rebalance_decisions_table`
7. Comparison — run three baselines: long TXN only, short KVUE only (FixRatio with negative weight pattern or direct), fixed 50/50 TXN+BIL; use `compare_strategies` and `plot_strategy_comparison_interactive`
8. Interpretation cell — markdown explaining spread P&L, hedge ratio, and when the strategy outperforms each baseline

#### Scenario: notebook runs end-to-end without errors
- **WHEN** the notebook is executed with `uv run jupyter nbconvert --to notebook --execute`
- **THEN** all cells complete without raising exceptions (requires network or cached YFinance data)

#### Scenario: notebook covers required sections
- **WHEN** notebook source is inspected
- **THEN** it contains cells for setup, data fetch, strategy construction, backtest, chart, table, and comparison

#### Scenario: DollarNeutral constructed with asymmetric book sizes
- **WHEN** the strategy cell is inspected
- **THEN** `long_book_size` and `short_book_size` are set so their ratio equals 1:1.135

#### Scenario: comparison includes three baselines
- **WHEN** comparison cells are inspected
- **THEN** long-TXN-only, short-KVUE-only, and a long-only TXN+BIL baseline are all present
