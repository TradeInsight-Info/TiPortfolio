# Purpose

TBD

## Requirements

### Requirement: VolatilityTargeting implements AllocationStrategy protocol

`VolatilityTargeting` SHALL implement the `AllocationStrategy` protocol with `get_symbols()` and `get_target_weights()`.

Constructor parameters:
- `symbols: list[str]` — assets to allocate to
- `lookback_days: int` — rolling window for realized volatility (e.g. 30)
- `target_vol: float | None = None` — optional annualised portfolio volatility target; if `None`, no scaling applied

#### Scenario: basic construction
- **WHEN** `VolatilityTargeting(symbols=["SPY", "GLD"], lookback_days=30)` is called
- **THEN** `get_symbols()` returns `["SPY", "GLD"]`

---

### Requirement: inverse-vol weighting when sufficient history exists

`get_target_weights()` SHALL compute inverse-vol weights using rolling realized volatility when `prices_history` has at least `lookback_days + 1` rows.

Formula:
```
daily_returns_i = prices_history[symbol].pct_change().dropna()
realized_vol_i  = std(daily_returns_i[-lookback_days:]) × √252
raw_weight_i    = 1 / realized_vol_i
w_i             = raw_weight_i / Σ raw_weight_j   (normalized, sums to 1.0)
```

#### Scenario: inverse-vol weights computed correctly
- **WHEN** `prices_history` has ≥ `lookback_days + 1` rows and assets have different volatilities
- **THEN** higher-volatility assets receive lower weights, lower-volatility assets receive higher weights, and weights sum to 1.0 ± 0.001

---

### Requirement: target_vol scaling when provided

When `target_vol` is set, apply a scaling factor after normalization:
```
portfolio_vol = √(wᵀ diag(σ²) w)   [diagonal covariance approximation]
scalar        = min(target_vol / portfolio_vol, 1.0)
w_i_scaled    = w_i × scalar
```
Residual weight `(1 − Σ w_i_scaled)` is NOT redistributed — strategy remains long-only with total weight ≤ 1.0 when target_vol constrains allocation.

#### Scenario: target_vol caps allocation
- **WHEN** `target_vol` is set and portfolio_vol exceeds target_vol
- **THEN** scalar < 1.0 and weights sum to less than 1.0

#### Scenario: target_vol has no effect when portfolio_vol is already below target
- **WHEN** `target_vol` is set and portfolio_vol ≤ target_vol
- **THEN** scalar = 1.0 and weights are the same as without target_vol

---

### Requirement: equal-weight fallback when history is insufficient

When `prices_history` is `None` or has fewer than `lookback_days + 1` rows, `get_target_weights()` SHALL return equal weights across all symbols and log a warning.

#### Scenario: None prices_history
- **WHEN** `get_target_weights()` is called without `prices_history` in context
- **THEN** returns `{symbol: 1/N for symbol in symbols}` summing to 1.0

#### Scenario: insufficient rows
- **WHEN** `prices_history` has fewer than `lookback_days + 1` rows
- **THEN** returns equal weights across all symbols

---

### Requirement: VolatilityTargeting exported from public API

`VolatilityTargeting` SHALL be importable from `tiportfolio` directly.

#### Scenario: public import works
- **WHEN** `from tiportfolio import VolatilityTargeting`
- **THEN** no ImportError is raised
