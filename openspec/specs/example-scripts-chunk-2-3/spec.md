# Spec: Example Scripts (Chunk 2–3)

## Purpose

This capability covers example scripts demonstrating advanced features of TiPortfolio, including quarterly signals, momentum selection, branching combinators, volatility targeting, dollar-neutral portfolios, VIX regime switching, and weekly rebalancing.

## Requirements

### Requirement: Quarterly ratio rebalance example

The project SHALL include `examples/10_quarterly_ratio.py` demonstrating `Signal.Quarterly` with `Weigh.Ratio` fixed weights.

#### Scenario: Script runs successfully
- **WHEN** `uv run python examples/10_quarterly_ratio.py` is executed with valid API access
- **THEN** the script SHALL print a summary and save a chart to `examples/10_quarterly_ratio.png`

### Requirement: Momentum selection example

The project SHALL include `examples/11_momentum_top_n.py` demonstrating `Select.Momentum` to pick top-N tickers by recent return.

#### Scenario: Script runs successfully
- **WHEN** `uv run python examples/11_momentum_top_n.py` is executed
- **THEN** the script SHALL print a summary and save a chart

### Requirement: Branching combinators example

The project SHALL include `examples/12_branching_skip_december.py` demonstrating `And`/`Not` combinators to skip rebalance in a specific month.

#### Scenario: Script runs successfully
- **WHEN** `uv run python examples/12_branching_skip_december.py` is executed
- **THEN** the script SHALL print a summary and save a chart

### Requirement: Volatility targeting example

The project SHALL include `examples/13_volatility_targeting.py` demonstrating `Weigh.BasedOnHV` to scale weights toward a target annualised volatility.

#### Scenario: Script runs successfully
- **WHEN** `uv run python examples/13_volatility_targeting.py` is executed
- **THEN** the script SHALL print a summary and save a chart

### Requirement: Dollar-neutral example

The project SHALL include `examples/14_dollar_neutral.py` demonstrating a parent/child tree portfolio with long and short legs using `Select.Momentum` and `Weigh.Equally(short=True)`.

#### Scenario: Script runs successfully
- **WHEN** `uv run python examples/14_dollar_neutral.py` is executed
- **THEN** the script SHALL print a summary and save a chart

### Requirement: VIX regime switching example

The project SHALL include `examples/15_vix_regime_switching.py` demonstrating `Signal.VIX` with two child portfolios for low-vol and high-vol regimes.

#### Scenario: Script runs successfully
- **WHEN** `uv run python examples/15_vix_regime_switching.py` is executed
- **THEN** the script SHALL print a summary and save a chart

### Requirement: Weekly rebalance example

The project SHALL include `examples/16_weekly_rebalance.py` demonstrating `Signal.Weekly` for weekly rebalancing.

#### Scenario: Script runs successfully
- **WHEN** `uv run python examples/16_weekly_rebalance.py` is executed
- **THEN** the script SHALL print a summary and save a chart
