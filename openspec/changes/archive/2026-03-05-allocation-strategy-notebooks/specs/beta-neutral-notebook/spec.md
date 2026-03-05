## ADDED Requirements

### Requirement: BetaNeutral notebook demonstrates dynamic beta-ranked long/short strategy

`notebooks/beta_neutral_dynamic.ipynb` SHALL demonstrate the `BetaScreenerStrategy` using a 20-stock universe, selecting 5 lowest-beta stocks as the long book and 5 highest-beta stocks as the short book each month, with `ScheduleBasedEngine` and `Schedule("month_mid")` and data from YFinance.

Universe (20 stocks + BIL as cash):
- Low-beta candidates: JNJ, PG, KO, WMT, VZ, ED, MCD, PEP
- High-beta candidates: NVDA, AMD, META, TSLA, MELI, PLTR, COIN, SMCI
- Mid-range: MSFT, AAPL, AMZN, GOOGL
- Cash: BIL
- Benchmark for beta computation: SPY (fetched separately, not traded)

Notebook sections (in order):
1. Setup — imports, cache, constants (`UNIVERSE` list, `CASH="BIL"`, `BENCHMARK="SPY"`, `N_LONG=5`, `N_SHORT=5`, `LOOKBACK=60`, `START`, `END`)
2. Data — fetch all universe symbols + BIL + SPY via YFinance; show shape
3. Benchmark prep — extract SPY close prices into a DataFrame for `benchmark_prices` constructor arg
4. Strategy — construct `BetaScreenerStrategy(universe=UNIVERSE, n_long=N_LONG, n_short=N_SHORT, cash_symbol=CASH, benchmark_prices=spy_df, lookback_days=LOOKBACK)`; wrap in `ScheduleBasedEngine` with `Schedule("month_mid")`
5. Run backtest — print `result.summary()`; note: all 21 symbols passed to `prices_df`
6. Portfolio chart — `plot_portfolio_with_assets_interactive` with rebalances marked
7. Rolling book composition — plot which symbols were in the long/short book each month (heatmap or grouped table)
8. Beta over time — plot rolling portfolio beta from rebalance decisions
9. Comparison — run two baselines: long SPY only, equal-weight universe; `compare_strategies` + `plot_strategy_comparison_interactive`
10. Disclaimer cell — markdown noting short selling requires a margin account

#### Scenario: notebook runs end-to-end without errors
- **WHEN** the notebook is executed with `uv run jupyter nbconvert --to notebook --execute`
- **THEN** all cells complete without raising exceptions

#### Scenario: all universe symbols fetched and passed to engine
- **WHEN** data cells are inspected
- **THEN** `prices_df` passed to `engine.run()` contains all 20 universe symbols plus BIL (21 columns)

#### Scenario: rolling book composition visualization present
- **WHEN** notebook cells are inspected
- **THEN** a cell shows which symbols were selected for long/short each rebalance (table or chart)

#### Scenario: comparison includes SPY and equal-weight baselines
- **WHEN** comparison cells are inspected
- **THEN** long-SPY and equal-weight-universe results are both present

#### Scenario: margin disclaimer present
- **WHEN** notebook markdown cells are inspected
- **THEN** a cell warns that short positions require a margin/prime brokerage account
