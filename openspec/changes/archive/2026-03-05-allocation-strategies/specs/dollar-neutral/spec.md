## ADDED Requirements

### Requirement: DollarNeutral implements AllocationStrategy protocol

`DollarNeutral` SHALL implement the `AllocationStrategy` protocol with `get_symbols()` and `get_target_weights()`.

Constructor parameters:
- `long_weights: dict[str, float]` — within-book proportions for long side (must sum to 1.0 ± 0.01)
- `short_weights: dict[str, float]` — within-book proportions for short side (must sum to 1.0 ± 0.01)
- `cash_symbol: str` — collateral symbol that absorbs residual weight (must not appear in long/short dicts)
- `book_size: float = 0.5` — fraction of equity in each book (default 50% long + 50% short)
- `tolerance: float = 0.05` — maximum net imbalance (as fraction of total equity) before rebalancing; if current imbalance ≤ tolerance, return current weights unchanged

#### Scenario: valid construction
- **WHEN** `DollarNeutral(long_weights={"SPY": 1.0}, short_weights={"QQQ": 1.0}, cash_symbol="BIL")` is called
- **THEN** `get_symbols()` returns all three symbols (SPY, QQQ, BIL in any order)

#### Scenario: construction validates long_weights sum
- **WHEN** `long_weights` values do not sum to 1.0 ± 0.01
- **THEN** `ValueError` is raised at construction

#### Scenario: construction validates short_weights sum
- **WHEN** `short_weights` values do not sum to 1.0 ± 0.01
- **THEN** `ValueError` is raised at construction

#### Scenario: construction validates cash_symbol not in long or short dicts
- **WHEN** `cash_symbol` appears as a key in `long_weights` or `short_weights`
- **THEN** `ValueError` is raised at construction

---

### Requirement: tolerance-band check gates rebalancing

`get_target_weights()` SHALL compute current net imbalance from `positions_dollars` and return current weights unchanged when within tolerance.

Imbalance formula:
```
long_value  = Σ positions_dollars[s]  for s in long_weights keys   (positive values)
short_value = |Σ positions_dollars[s]| for s in short_weights keys  (negative values, take abs)
imbalance   = abs(long_value - short_value) / total_equity
```

When `imbalance ≤ tolerance` AND `positions_dollars` is non-empty (not the initial allocation):
- Return current weights: `{s: positions_dollars[s] / total_equity for s in all_symbols}`

When `imbalance > tolerance` OR `positions_dollars` is empty:
- Return target weights (see next requirement)

#### Scenario: within tolerance returns current weights
- **WHEN** `abs(long_value - short_value) / total_equity <= tolerance`
- **THEN** returned weights match `positions_dollars / total_equity` (no trades triggered)

#### Scenario: outside tolerance returns target weights
- **WHEN** `abs(long_value - short_value) / total_equity > tolerance`
- **THEN** returned weights are the balanced target weights

#### Scenario: empty positions_dollars triggers initial target weights
- **WHEN** `positions_dollars` is empty (initial allocation)
- **THEN** target weights are returned regardless of tolerance

---

### Requirement: target weights always sum to 1.0

When returning target weights, `get_target_weights()` SHALL produce weights that sum to 1.0 by assigning residual to `cash_symbol`.

Formula:
```
long symbol i:  weight = book_size × long_weights[i]     (positive)
short symbol j: weight = −book_size × short_weights[j]   (negative)
cash:           weight = 1.0 − (Σ_long_weights + Σ_short_weights_signed)
              = 1.0 − book_size × (1.0 − 1.0) = 1.0   [balanced default]
```

When `book_size=0.5`, `long_weights={"SPY": 1.0}`, `short_weights={"QQQ": 1.0}`:
- SPY = +0.5, QQQ = −0.5, BIL = 1.0 → sum = 1.0 ✓

#### Scenario: balanced books produce cash weight of 1.0
- **WHEN** `book_size=0.5` and both books are fully allocated within themselves
- **THEN** `cash_symbol` weight equals `1.0`

#### Scenario: total target weights sum to 1.0
- **WHEN** target weights are returned
- **THEN** `sum(weights.values()) == 1.0 ± 0.001`

#### Scenario: short symbols have negative weights
- **WHEN** target weights are returned
- **THEN** weights for all short symbols are negative

---

### Requirement: DollarNeutral exported from public API

`DollarNeutral` SHALL be importable from `tiportfolio` directly.

#### Scenario: public import works
- **WHEN** `from tiportfolio import DollarNeutral`
- **THEN** no ImportError is raised
