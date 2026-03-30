## ADDED Requirements

### Requirement: Recursive mark-to-market for parent portfolios
`mark_to_market` SHALL compute parent equity as the sum of children equity, recursing into each child first. Leaf equity = cash + sum(qty * price).

#### Scenario: Parent with two leaf children
- **WHEN** a parent has two children with equity 6000 and 4000
- **THEN** parent equity is 10000

#### Scenario: Leaf mark-to-market unchanged
- **WHEN** a leaf has cash=5000, position QQQ=10 shares at price 200
- **THEN** equity is 7000 (5000 + 10*200)

#### Scenario: Parent with zero-equity deselected child
- **WHEN** a parent has one active child (equity 10000) and one deselected child (equity 0)
- **THEN** parent equity is 10000

### Requirement: Parent equity allocation redistributes capital via 4-step process
`allocate_equity_to_children` SHALL: (1) liquidate deselected children, (2) compute total equity from all children, (3) redistribute to selected children by weight, (4) zero deselected children.

#### Scenario: Equal split between two children
- **WHEN** parent has weights `{child_a: 0.5, child_b: 0.5}` and total equity is 10000
- **THEN** child_a.equity = 5000, child_b.equity = 5000

#### Scenario: Deselected child is liquidated and zeroed
- **WHEN** parent deselects child_b (which holds positions) and selects only child_a with weight 1.0
- **THEN** child_b positions are sold (fees deducted), recovered proceeds added to total, child_a.equity = total, child_b.equity = 0, child_b.cash = 0

#### Scenario: Parent cash invariant
- **WHEN** `allocate_equity_to_children` runs
- **THEN** parent portfolio.cash remains 0.0 throughout

### Requirement: Child liquidation sells all positions
`_liquidate_child` SHALL sell all positions at closing price, deduct fees, and accumulate proceeds in `child.cash`. After liquidation, `child.positions` is empty.

#### Scenario: Liquidate child with one position
- **WHEN** child holds 100 shares of QQQ at price 200, fee_per_share=0.0035
- **THEN** child.cash increases by (100 * 200 - 100 * 0.0035), child.positions = {}

### Requirement: _allocate_children callback wired in engine context
`_run_single` SHALL set `_allocate_children=allocate_equity_to_children` in the Context passed to `_evaluate_node`, so `Action.Rebalance` can dispatch parent-level capital allocation.

#### Scenario: Parent portfolio runs without RuntimeError
- **WHEN** a parent portfolio with `[Signal.Monthly(), Select.All(), Weigh.Equally(), Action.Rebalance()]` is run
- **THEN** `Action.Rebalance` calls `_allocate_children` without error

### Requirement: Parent portfolio initialisation
`_run_single` SHALL detect parent portfolios and initialise them with `cash=0.0`, `equity=initial_capital`, `positions={}`. Children SHALL be initialised with `cash=0.0`, `equity=0.0`, `positions={}`.

#### Scenario: Parent root portfolio
- **WHEN** a parent portfolio is passed to `Backtest` with `initial_capital=10000`
- **THEN** root.cash=0.0, root.equity=10000; each child starts with equity=0.0

### Requirement: execute_leaf_trades uses fractional shares
`execute_leaf_trades` SHALL use `target_value / price` (fractional) instead of `math.floor(target_value / price)`.

#### Scenario: Fractional share allocation
- **WHEN** target_value=1000, price=33.33
- **THEN** target_qty ≈ 30.003 (not floored to 30)
