## Purpose

Defines the `--ratio` CLI option that controls how portfolio weights are determined: equal, explicit ratios, ERC risk parity, or volatility-targeted (HV).

## Requirements

### Requirement: Equal weighting
`--ratio equal` SHALL use `Weigh.Equally()`.

#### Scenario: Equal weight
- **WHEN** `--ratio equal` is passed
- **THEN** the backtest SHALL use `Weigh.Equally()`

### Requirement: Explicit ratio weighting
`--ratio 0.7,0.2,0.1` SHALL use `Weigh.Ratio(weights=)` with weights mapped positionally to tickers.

#### Scenario: Explicit ratios
- **WHEN** `--tickers QQQ,BIL,GLD --ratio 0.7,0.2,0.1` is passed
- **THEN** the backtest SHALL use `Weigh.Ratio({"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1})`

#### Scenario: Ratio count mismatch
- **WHEN** `--tickers QQQ,BIL,GLD --ratio 0.7,0.2` is passed (2 ratios for 3 tickers)
- **THEN** an error SHALL indicate the count mismatch

### Requirement: ERC risk parity weighting
`--ratio erc` SHALL use `Weigh.ERC(lookback=)` with the `--lookback` option.

#### Scenario: ERC with lookback
- **WHEN** `--ratio erc --lookback 90d` is passed
- **THEN** the backtest SHALL use `Weigh.ERC(lookback=pd.DateOffset(days=90))`

#### Scenario: ERC default lookback
- **WHEN** `--ratio erc` is passed without `--lookback`
- **THEN** the backtest SHALL use `Weigh.ERC(lookback=pd.DateOffset(days=60))` as default

### Requirement: Volatility-target weighting
`--ratio hv` SHALL use `Weigh.BasedOnHV(initial_ratio=, target_hv=, lookback=)`.

#### Scenario: HV with target
- **WHEN** `--tickers QQQ,BIL,GLD --ratio hv --target-hv 0.10 --lookback 90d` is passed
- **THEN** the backtest SHALL use `Weigh.BasedOnHV` with equal initial ratios, target_hv=0.10, lookback=90 days

#### Scenario: HV requires --target-hv
- **WHEN** `--ratio hv` is passed without `--target-hv`
- **THEN** an error SHALL indicate that `--target-hv` is required

### Requirement: Default weighting is equal
When `--ratio` is not specified, the CLI SHALL default to `Weigh.Equally()`.

#### Scenario: No ratio specified
- **WHEN** no `--ratio` flag is passed
- **THEN** the backtest SHALL use `Weigh.Equally()`
