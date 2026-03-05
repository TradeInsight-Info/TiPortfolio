## MODIFIED Requirements

### Requirement: DollarNeutral implements AllocationStrategy protocol

`DollarNeutral` SHALL implement the `AllocationStrategy` protocol with `get_symbols()` and `get_target_weights()`.

Constructor parameters:
- `long_weights: dict[str, float]` — within-book proportions for long side (must sum to 1.0 ± 0.01)
- `short_weights: dict[str, float]` — within-book proportions for short side (must sum to 1.0 ± 0.01)
- `cash_symbol: str` — collateral symbol that absorbs residual weight (must not appear in long/short dicts)
- `book_size: float = 0.5` — default fraction of equity for each book when per-side sizes are not specified
- `long_book_size: float | None = None` — fraction of equity for the long book; overrides `book_size` for the long side when set
- `short_book_size: float | None = None` — fraction of equity for the short book; overrides `book_size` for the short side when set
- `tolerance: float = 0.05` — maximum net imbalance (as fraction of total equity) before rebalancing; if current imbalance ≤ tolerance, return current weights unchanged

When `long_book_size` is `None`, the effective long book size is `book_size`.
When `short_book_size` is `None`, the effective short book size is `book_size`.

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

#### Scenario: asymmetric book sizes override book_size
- **WHEN** `DollarNeutral(long_weights={"TXN": 1.0}, short_weights={"KVUE": 1.0}, cash_symbol="BIL", long_book_size=0.468, short_book_size=0.532)` is called
- **THEN** target weights are: TXN = +0.468, KVUE = −0.532, BIL = 1.064 (sum = 1.0)

#### Scenario: omitting per-side sizes falls back to book_size
- **WHEN** `long_book_size=None` and `short_book_size=None`
- **THEN** both sides use `book_size` (existing behavior unchanged)

---

### Requirement: target weights always sum to 1.0

When returning target weights, `get_target_weights()` SHALL produce weights that sum to 1.0 by assigning residual to `cash_symbol`, using per-side book sizes.

Formula:
```
lbs = long_book_size if long_book_size is not None else book_size
sbs = short_book_size if short_book_size is not None else book_size

long symbol i:  weight = lbs × long_weights[i]     (positive)
short symbol j: weight = −sbs × short_weights[j]   (negative)
cash:           weight = 1.0 − net
```

#### Scenario: symmetric books produce cash weight of 1.0
- **WHEN** `book_size=0.5`, `long_book_size=None`, `short_book_size=None`, both books fully allocated
- **THEN** `cash_symbol` weight equals `1.0`

#### Scenario: asymmetric books produce cash absorbing net imbalance
- **WHEN** `long_book_size=0.468`, `short_book_size=0.532`
- **THEN** `cash_symbol` weight equals `1.0 − (0.468 − 0.532) = 1.064`

#### Scenario: total target weights sum to 1.0
- **WHEN** target weights are returned (symmetric or asymmetric)
- **THEN** `sum(weights.values()) == 1.0 ± 0.001`

#### Scenario: short symbols have negative weights
- **WHEN** target weights are returned
- **THEN** weights for all short symbols are negative

---

### Requirement: tolerance-band check gates rebalancing

`get_target_weights()` SHALL compute current net imbalance from `positions_dollars` and return current weights unchanged when within tolerance.

Imbalance formula uses per-side target book sizes (lbs, sbs):
```
long_value  = Σ positions_dollars[s]  for s in long_weights keys
short_value = |Σ positions_dollars[s]| for s in short_weights keys
imbalance   = abs(long_value - short_value) / total_equity
```

#### Scenario: within tolerance returns current weights
- **WHEN** `abs(long_value - short_value) / total_equity <= tolerance` and positions non-empty
- **THEN** returned weights match `positions_dollars / total_equity` (no trades)

#### Scenario: outside tolerance returns target weights
- **WHEN** `abs(long_value - short_value) / total_equity > tolerance`
- **THEN** returned weights are the target weights computed with lbs/sbs

#### Scenario: empty positions_dollars triggers initial target weights
- **WHEN** `positions_dollars` is empty
- **THEN** target weights are returned regardless of tolerance

---

### Requirement: DollarNeutral exported from public API

`DollarNeutral` SHALL be importable from `tiportfolio` directly.

#### Scenario: public import works
- **WHEN** `from tiportfolio import DollarNeutral`
- **THEN** no ImportError is raised
