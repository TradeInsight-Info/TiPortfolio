## ADDED Requirements

### Requirement: execute_leaf_trades records trade details

`execute_leaf_trades` SHALL capture a trade record for each position change. Each record SHALL contain: `date`, `portfolio` (name), `ticker`, `qty_before`, `qty_after`, `delta`, `price`, `fee`, `equity_before`, `equity_after`.

#### Scenario: New position opened
- **WHEN** a ticker is selected with weight > 0 and has no prior position
- **THEN** a trade record SHALL be created with `qty_before=0`, `qty_after=target_qty`, `delta=target_qty`

#### Scenario: Position adjusted
- **WHEN** a ticker's target weight changes resulting in a different quantity
- **THEN** a trade record SHALL be created with the correct `qty_before`, `qty_after`, and `delta`

#### Scenario: Position closed
- **WHEN** a ticker is not in the new selection but has an existing position
- **THEN** a trade record SHALL be created with `qty_after=0` and `delta=-qty_before`

### Requirement: _SingleResult exposes trades property

`_SingleResult` SHALL have a `trades` property that returns a `Trades` instance wrapping all trade records from the backtest run.

#### Scenario: Access trades after backtest
- **WHEN** `result[0].trades` is accessed
- **THEN** a `Trades` instance SHALL be returned containing all trade records

### Requirement: Trades wraps DataFrame with delegation

The `Trades` class SHALL wrap a `pd.DataFrame` and delegate attribute access via `__getattr__`. Standard DataFrame operations (`.head()`, `.tail()`, `.describe()`, column access) SHALL work directly on a `Trades` instance.

#### Scenario: DataFrame method delegation
- **WHEN** `result[0].trades.head(5)` is called
- **THEN** the first 5 rows of the underlying DataFrame SHALL be returned

#### Scenario: Column access
- **WHEN** `result[0].trades["ticker"]` is called
- **THEN** the ticker column Series SHALL be returned

### Requirement: Trades.sample(n) returns top and bottom rebalances

`Trades.sample(n)` SHALL return a DataFrame containing the top-N and bottom-N rebalances ranked by equity return (`equity_after - equity_before`). When `2*n >= len(trades)`, duplicates SHALL be removed using `~df.index.duplicated()`.

#### Scenario: sample(5) with many trades
- **WHEN** `result[0].trades.sample(5)` is called on a backtest with > 10 trades
- **THEN** a DataFrame with 10 rows SHALL be returned (5 best + 5 worst by equity return)

#### Scenario: sample(n) with overlap
- **WHEN** `result[0].trades.sample(n)` is called where `2*n >= len(trades)`
- **THEN** duplicates SHALL be removed and a DataFrame with `<= len(trades)` rows returned
