## ADDED Requirements

### Requirement: Backtest constructor validates data and accepts config
The system SHALL provide `Backtest(portfolio, data, fee_per_share=None, config=None)`. It SHALL call `validate_data(data)` at construction. If `config` is None, it SHALL use `TiConfig()`. If `fee_per_share` is provided, it SHALL override `config.fee_per_share`.

#### Scenario: Valid construction
- **WHEN** `Backtest(portfolio, data)` is called with aligned data
- **THEN** the Backtest is created with default TiConfig

#### Scenario: Misaligned data rejected
- **WHEN** `Backtest(portfolio, data)` is called with misaligned price DataFrames
- **THEN** `ValueError` is raised at construction time

### Requirement: Simulation loop runs day-by-day
The system SHALL iterate over every trading day (sorted union of all DatetimeIndex values across tickers). For each day: (1) mark-to-market, (2) record equity, (3) evaluate the portfolio's algo queue.

#### Scenario: 20-day backtest
- **WHEN** a Backtest with 20 trading days of data is run
- **THEN** the equity curve has 20 entries, one per trading day

### Requirement: mark_to_market computes leaf portfolio equity
For leaf portfolios, the system SHALL compute `equity = cash + sum(qty * close_price for each position)` on every bar.

#### Scenario: Portfolio with positions
- **WHEN** portfolio has cash=5000, positions={"QQQ": 10} and QQQ closes at 100
- **THEN** after mark_to_market, equity equals 6000

#### Scenario: Empty portfolio
- **WHEN** portfolio has cash=10000, positions={} (before first rebalance)
- **THEN** after mark_to_market, equity equals 10000

### Requirement: execute_leaf_trades computes deltas and updates positions
The system SHALL compute target positions from `context.weights` and current equity, then trade the delta. Fees are deducted from cash. New positions replace old ones.

#### Scenario: First rebalance from cash
- **WHEN** portfolio has cash=10000, positions={}, and weights={"QQQ": 0.5, "BIL": 0.5} with QQQ at 100 and BIL at 50
- **THEN** target qty for QQQ = floor(5000/100)=50, BIL = floor(5000/50)=100; positions updated; cash reduced by total cost + fees

#### Scenario: Rebalance with existing positions
- **WHEN** portfolio holds QQQ=50 and weights shift to QQQ=0.3
- **THEN** excess QQQ shares are sold; proceeds + fee adjustment update cash

### Requirement: ti.run executes backtests and returns results
The system SHALL provide `ti.run(*tests: Backtest)` that runs each backtest and returns a `BacktestResult`.

#### Scenario: Single backtest
- **WHEN** `ti.run(backtest)` is called with one Backtest
- **THEN** a BacktestResult is returned containing one _SingleResult

### Requirement: Portfolio initialised with config.initial_capital
At the start of simulation, the system SHALL set leaf portfolio `cash = config.initial_capital` and `equity = config.initial_capital`.

#### Scenario: Default initial capital
- **WHEN** a backtest starts with default TiConfig (initial_capital=10_000)
- **THEN** portfolio.cash is 10_000 and portfolio.equity is 10_000 on the first bar
