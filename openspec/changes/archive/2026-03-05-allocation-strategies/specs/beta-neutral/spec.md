## ADDED Requirements

### Requirement: BetaNeutral implements AllocationStrategy protocol

`BetaNeutral` SHALL implement the `AllocationStrategy` protocol with `get_symbols()` and `get_target_weights()`.

Constructor parameters:
- `long_symbols: list[str]` — symbols to hold long
- `short_symbols: list[str]` — symbols to hold short
- `cash_symbol: str` — collateral symbol; must not appear in long/short lists
- `benchmark_symbol: str = "SPY"` — index used to compute beta; fetched internally, NOT in `get_symbols()`
- `benchmark_prices: pd.DataFrame | None = None` — optional pre-loaded benchmark OHLCV DataFrame (indexed by date); if provided, no internal fetch is performed
- `lookback_days: int = 60` — rolling window for OLS beta computation
- `book_size: float = 0.5` — gross exposure per side (default 50% long + 50% short)

`get_symbols()` returns only `long_symbols + short_symbols + [cash_symbol]`. The `benchmark_symbol` does NOT appear in `get_symbols()` and does NOT appear in the returned weights dict.

#### Scenario: valid construction
- **WHEN** `BetaNeutral(long_symbols=["AAPL"], short_symbols=["QQQ"], cash_symbol="BIL")` is called
- **THEN** `get_symbols()` returns `["AAPL", "QQQ", "BIL"]` (no SPY)

#### Scenario: construction validates no overlap between long, short, and cash
- **WHEN** any symbol appears in more than one of `long_symbols`, `short_symbols`, `cash_symbol`
- **THEN** `ValueError` is raised at construction

---

### Requirement: benchmark prices obtained without appearing in price universe

When `benchmark_prices` is `None`, `get_target_weights()` SHALL call `fetch_prices([benchmark_symbol], start, end)` using the date range of `prices_history` to obtain benchmark close prices. When `benchmark_prices` is provided at construction, use that directly (no fetch).

The result is cached on the strategy instance to avoid redundant fetches within a single backtest run.

#### Scenario: internal fetch used when benchmark_prices not provided
- **WHEN** `BetaNeutral(..., benchmark_prices=None)` and `prices_history` is available
- **THEN** `fetch_prices` is called with `[benchmark_symbol]` and the date range of `prices_history`

#### Scenario: pre-loaded prices bypass fetch
- **WHEN** `BetaNeutral(..., benchmark_prices=spy_df)` is constructed
- **THEN** `fetch_prices` is never called; `spy_df` is used directly for beta computation

---

### Requirement: beta-neutral weight computation using OLS rolling beta

`get_target_weights()` SHALL compute OLS betas and solve for zero-net-beta weights when sufficient history is available.

Beta formula (over `lookback_days` window):
```
β_i = Cov(r_i, r_benchmark) / Var(r_benchmark)
```

For two-asset case (one long `L`, one short `S`), solve analytically:
```
w_L × β_L + w_S × β_S = 0
w_L + |w_S| = 2 × book_size

→ w_L = 2 × book_size × β_S / (β_S − β_L)   [β_L ≠ β_S]
  w_S = −(2 × book_size − w_L)
```
For N-asset case: equal weights within each book (simplified; full OLS solve is a non-goal).

Cash weight:
```
cash = 1.0 − (Σ w_long + Σ w_short)   [net exposure]
```

#### Scenario: two-symbol beta-neutral produces zero net beta
- **WHEN** `prices_history` and benchmark prices are sufficient (≥ `lookback_days + 1` rows)
- **THEN** `sum(w_i × β_i) ≈ 0` (within 1e-9 floating-point tolerance)

#### Scenario: total weights sum to 1.0
- **WHEN** `get_target_weights()` is called with sufficient history
- **THEN** `sum(weights.values()) == 1.0 ± 0.001`

#### Scenario: benchmark_symbol not in returned weights
- **WHEN** `get_target_weights()` is called
- **THEN** the returned dict contains only long, short, and cash symbols

---

### Requirement: equal-weight fallback when history is insufficient

When `prices_history` is `None`, has fewer than `lookback_days + 1` rows, or benchmark prices cannot be obtained, `get_target_weights()` SHALL fall back to equal weights within each book and log a warning.

Fallback:
```
long_symbols:  each gets +book_size / len(long_symbols)
short_symbols: each gets −book_size / len(short_symbols)
cash:          1.0 − net_exposure
```

#### Scenario: fallback on None prices_history
- **WHEN** `prices_history` is not in context
- **THEN** equal weights within each book, sum = 1.0

#### Scenario: fallback on insufficient history
- **WHEN** `prices_history` has fewer than `lookback_days + 1` rows
- **THEN** equal weights within each book

#### Scenario: fallback when benchmark prices unavailable
- **WHEN** `fetch_prices` raises or returns empty and no `benchmark_prices` was provided
- **THEN** equal-weight fallback is applied with a warning

---

### Requirement: BetaNeutral exported from public API

`BetaNeutral` SHALL be importable from `tiportfolio` directly.

#### Scenario: public import works
- **WHEN** `from tiportfolio import BetaNeutral`
- **THEN** no ImportError is raised
