## Purpose

Specification for the `BetaScreenerStrategy` utility that implements a dynamic long/short allocation strategy using rolling OLS beta ranking.

## Requirements

### Requirement: BetaScreenerStrategy implements AllocationStrategy protocol

`BetaScreenerStrategy` in `src/tiportfolio/utils/beta_screener.py` SHALL implement `get_symbols()` and `get_target_weights()` compatible with the `AllocationStrategy` protocol.

Constructor parameters:
- `universe: list[str]` — full set of candidate stock symbols to rank by beta each rebalance
- `n_long: int` — number of lowest-beta symbols to go long each rebalance
- `n_short: int` — number of highest-beta symbols to go short each rebalance
- `cash_symbol: str` — absorbs residual weight; must not appear in `universe`
- `benchmark_prices: pd.DataFrame` — OHLCV DataFrame with a `close` column for the benchmark; date index must overlap with `prices_history`
- `lookback_days: int = 60` — rolling window for OLS beta computation
- `book_size: float = 0.5` — notional fraction of equity in the long book; short book is scaled to achieve beta neutrality

#### Scenario: get_symbols returns full universe plus cash
- **WHEN** `BetaScreenerStrategy(universe=["A","B","C"], n_long=1, n_short=1, cash_symbol="CASH", benchmark_prices=bp)` is called
- **THEN** `get_symbols()` returns `["A", "B", "C", "CASH"]` (universe + cash, benchmark excluded)

#### Scenario: cash_symbol must not be in universe
- **WHEN** `cash_symbol` is also in `universe`
- **THEN** `ValueError` is raised at construction

#### Scenario: n_long + n_short must not exceed universe size
- **WHEN** `n_long + n_short > len(universe)`
- **THEN** `ValueError` is raised at construction

---

### Requirement: rolling OLS beta computed from prices_history

At each rebalance `get_target_weights()` SHALL compute rolling OLS beta for every symbol in `universe` using the last `lookback_days` rows of `prices_history` and the `benchmark_prices` DataFrame.

Beta formula: `β_i = Cov(r_i, r_bench) / Var(r_bench)` over the lookback window.

#### Scenario: beta computed from prices_history context
- **WHEN** `prices_history` contains `lookback_days + 1` or more rows for all universe symbols
- **THEN** a beta value is computed for every symbol in `universe`

#### Scenario: fallback to equal-weight when insufficient history
- **WHEN** `prices_history` has fewer than `lookback_days + 1` rows, or is absent from context
- **THEN** returns equal-weight within each book (equal long weights, equal short weights) with `UserWarning`

#### Scenario: fallback when benchmark has no overlap
- **WHEN** `benchmark_prices` index has no dates in common with `prices_history` after lookback
- **THEN** returns equal-weight fallback with `UserWarning`

---

### Requirement: dynamic long/short book selection by beta rank

At each rebalance the strategy SHALL select symbols for long and short books based on current beta rank.

- Long book: `n_long` symbols with **lowest** beta values
- Short book: `n_short` symbols with **highest** beta values
- Remaining `universe` symbols receive weight `0.0`

#### Scenario: long book holds lowest-beta symbols
- **WHEN** betas are computed and `n_long=3`
- **THEN** the 3 symbols with the smallest beta values have positive weights; all others have 0 or negative weights

#### Scenario: short book holds highest-beta symbols
- **WHEN** betas are computed and `n_short=3`
- **THEN** the 3 symbols with the largest beta values have negative weights

---

### Requirement: beta-neutral weight sizing

Weights SHALL be scaled so that `Σ w_i × β_i ≈ 0` across the selected portfolio.

Sizing formula:
```
avg_beta_long  = mean(beta[s] for s in long book)
avg_beta_short = mean(beta[s] for s in short book)
short_book_size = book_size × avg_beta_long / avg_beta_short   [clamped to (0.1, 2.0)]

w_long_i  = +book_size / n_long    (equal within long book)
w_short_j = -short_book_size / n_short  (equal within short book)
cash      = 1.0 - sum(all non-cash weights)
```

#### Scenario: portfolio beta approximately zero
- **WHEN** `get_target_weights()` returns weights with sufficient history
- **THEN** `abs(sum(w_i * beta_i for non-cash symbols)) < 0.1` (within 10 bps of zero)

#### Scenario: weights sum to 1.0
- **WHEN** target weights are returned
- **THEN** `sum(weights.values()) == 1.0 ± 0.001`

#### Scenario: all universe symbols zero-weighted except selected books
- **WHEN** target weights are returned
- **THEN** exactly `n_long + n_short` symbols have non-zero non-cash weights

---

### Requirement: BetaScreenerStrategy exported from public API

`BetaScreenerStrategy` SHALL be importable from `tiportfolio` directly.

#### Scenario: public import works
- **WHEN** `from tiportfolio import BetaScreenerStrategy`
- **THEN** no ImportError is raised
