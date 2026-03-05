## ADDED Requirements

### Requirement: VolatilityTargeting notebook demonstrates inverse-vol QQQ/BIL/GLD

`notebooks/volatility_targeting_qqq_bil_gld.ipynb` SHALL demonstrate the `VolatilityTargeting` strategy on QQQ, BIL, GLD using `ScheduleBasedEngine` with `Schedule("month_mid")` and data from YFinance.

Notebook sections (in order):
1. Setup — imports, cache, constants (`SYMBOLS=["QQQ","BIL","GLD"]`, `START`, `END`, `LOOKBACK=60`, optional `TARGET_VOL=None`)
2. Data — fetch via YFinance; show shape and date range
3. Strategy — construct `VolatilityTargeting(symbols=SYMBOLS, lookback_days=LOOKBACK, target_vol=TARGET_VOL)` with `Schedule("month_mid")`
4. Run backtest — print `result.summary()`
5. Portfolio chart — `plot_portfolio_with_assets_interactive` with rebalances marked
6. Weight evolution — plot how weights shift over time (QQQ weight drops when QQQ vol rises)
7. Rebalance table — show selected rebalance decisions including computed weights
8. Comparison — run two baselines: fixed 70/20/10 (FixRatio), long QQQ only; `compare_strategies` + `plot_strategy_comparison_interactive`
9. Target vol demo cell — show how setting `TARGET_VOL=0.10` de-levers the portfolio during high-vol regimes
10. Interpretation cell — markdown explaining inverse-vol weighting, when BIL/GLD get higher weight, and target_vol mechanics

#### Scenario: notebook runs end-to-end without errors
- **WHEN** the notebook is executed with `uv run jupyter nbconvert --to notebook --execute`
- **THEN** all cells complete without raising exceptions

#### Scenario: weight evolution plot present
- **WHEN** notebook cells are inspected
- **THEN** a cell reconstructs per-rebalance weights from `rebalance_decisions` and plots them as a stacked area or line chart

#### Scenario: comparison includes fixed-weight and buy-and-hold baselines
- **WHEN** comparison cells are inspected
- **THEN** fixed 70/20/10 and long-QQQ-only results are both present

#### Scenario: target_vol section demonstrates de-levering
- **WHEN** the target_vol demo cell is run with `TARGET_VOL=0.10`
- **THEN** a comparison is shown between the uncapped strategy and the target_vol capped version
