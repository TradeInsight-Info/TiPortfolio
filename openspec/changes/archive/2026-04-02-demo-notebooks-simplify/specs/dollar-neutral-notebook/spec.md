## ADDED Requirements

### Requirement: Dollar-neutral pair trade notebook
The notebook SHALL demonstrate a dollar-neutral long/short pair trade (TXN long / KVUE short) using a parent/child portfolio tree with controlled book sizes.

#### Scenario: Data loading for pair trade
- **WHEN** loading price data
- **THEN** the notebook SHALL fetch TXN, KVUE, and BIL data via `ti.fetch_data()` (live fetch since KVUE is not in CSV cache, listed Sept 2023)

#### Scenario: Long child portfolio
- **WHEN** building the long leg
- **THEN** a child portfolio SHALL hold TXN using `Weigh.Equally()` and `Action.Rebalance()`

#### Scenario: Short child portfolio
- **WHEN** building the short leg
- **THEN** a child portfolio SHALL hold KVUE using `Weigh.Equally(short=True)` and `Action.Rebalance()`

#### Scenario: Parent with hedge ratio
- **WHEN** building the parent portfolio
- **THEN** it SHALL use `Weigh.Ratio()` to control the long/short book sizes based on a hedge ratio (~1:1.135), with `Signal.Monthly()` and `Action.Rebalance()`

#### Scenario: Baseline comparisons
- **WHEN** comparing strategies
- **THEN** the notebook SHALL include a long-only TXN baseline and a 50/50 TXN+BIL baseline

#### Scenario: Results exploration
- **WHEN** displaying results
- **THEN** the notebook SHALL show `summary()`, `plot()`, `plot_security_weights()`, and `trades.sample()`
