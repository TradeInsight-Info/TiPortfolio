# Daily Carry Costs

**Purpose**: Defines daily short borrow and leverage loan cost deduction for leaf portfolios with short or leveraged positions.

## Requirements

### Requirement: Daily short borrow cost deducted from cash
For each short position (negative qty), `deduct_daily_carry_costs` SHALL deduct `abs(qty * price) * stock_borrow_rate / bars_per_year` from `portfolio.cash`.

#### Scenario: Short 100 shares at price 200
- **WHEN** position is -100 shares at price 200, stock_borrow_rate=0.07, bars_per_year=252
- **THEN** daily cost = abs(-100 * 200) * 0.07 / 252 ≈ 5.56 deducted from cash

#### Scenario: No cost for long positions
- **WHEN** position is +100 shares (positive qty)
- **THEN** no short borrow cost is deducted

### Requirement: Daily leverage loan cost deducted when long exposure exceeds equity
When total long market value exceeds portfolio equity, `deduct_daily_carry_costs` SHALL deduct `(long_value - equity) * loan_rate / bars_per_year` from `portfolio.cash`.

#### Scenario: Leveraged long position
- **WHEN** long_value=15000, equity=10000, loan_rate=0.0514, bars_per_year=252
- **THEN** daily cost = (15000 - 10000) * 0.0514 / 252 ≈ 1.02 deducted from cash

#### Scenario: No leverage cost when long_value <= equity
- **WHEN** long_value=8000, equity=10000
- **THEN** no leverage loan cost is deducted

### Requirement: Carry costs applied recursively for parent portfolios
`deduct_daily_carry_costs` SHALL recurse into children for parent nodes (parent nodes never hold positions directly).

#### Scenario: Parent with two leaf children
- **WHEN** parent has two children, one with short positions and one without
- **THEN** carry costs are deducted only from the child with short positions

### Requirement: Carry costs run every bar after mark-to-market
In the engine loop, `deduct_daily_carry_costs` SHALL run after `mark_to_market` and before algo evaluation on every trading day.

#### Scenario: Loop ordering
- **WHEN** the engine processes a trading day
- **THEN** the order is: mark_to_market → deduct_daily_carry_costs → record_equity → evaluate_node
