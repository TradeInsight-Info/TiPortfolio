## Context

Three allocation strategies (VolatilityTargeting, DollarNeutral, BetaNeutral) were recently added to `allocation.py`. The backtest engine (`run_backtest`) now injects `prices_history` in the context dict on every rebalance call, enabling strategies to use rolling statistics.

Current gaps that block the notebooks:
1. `DollarNeutral` has a single `book_size` applied symmetrically to both sides. A TXN/KVUE hedge ratio of 1:1.135 requires independent per-side sizing.
2. `BetaNeutral` has fixed `long_symbols` / `short_symbols` set at construction time. A screener that re-ranks a stock universe each month and updates the long/short books needs a different design.
3. No demonstration notebooks exist for any of the three new strategies.

## Goals / Non-Goals

**Goals:**
- Extend `DollarNeutral` with `long_book_size` / `short_book_size` (backward-compatible)
- Build a `BetaScreenerStrategy` utility (notebook-level class) that dynamically selects the long/short book from a fixed universe each rebalance, using rolling OLS beta vs SPY
- Three notebooks: DollarNeutral TXN/KVUE, VolatilityTargeting QQQ/BIL/GLD, BetaNeutral dynamic screener
- All notebooks: `Schedule("month_mid")`, data via YFinance + disk cache, comparisons to baselines

**Non-Goals:**
- Modifying `BetaNeutral` core class (the screener is notebook-level)
- Intraday or tick-level data
- Live trading integration
- Universe optimization (a fixed 20-stock universe is sufficient to demonstrate the strategy)

## Decisions

**1. DollarNeutral asymmetric sizing via `long_book_size` / `short_book_size`**

Add two optional fields that override `book_size` per side:

```python
long_book_size: float | None = None   # defaults to book_size if None
short_book_size: float | None = None  # defaults to book_size if None
```

In `_target_weights()`:
```python
lbs = self.long_book_size if self.long_book_size is not None else self.book_size
sbs = self.short_book_size if self.short_book_size is not None else self.book_size
weights[s] = lbs * long_weights[s]
weights[s] = -sbs * short_weights[s]
cash = 1.0 - sum(weights.values())
```

For TXN:KVUE ratio 1:1.135 with total notional 1.0:
- `long_book_size = 1 / (1 + 1.135) ≈ 0.468`
- `short_book_size = 1.135 / (1 + 1.135) ≈ 0.532`
- Result: TXN = +0.468, KVUE = −0.532, BIL = 1.064 → sum = 1.0 ✓

The tolerance-band imbalance check is updated to use the per-side sizes for consistency.

**2. `BetaScreenerStrategy` as a notebook-level class (not modifying BetaNeutral)**

`BetaNeutral` requires fixed symbols because `get_symbols()` is called once by the engine at startup to determine which columns appear in `prices_df`. For dynamic stock selection we use a wrapper pattern:

- `get_symbols()` returns the **full universe** (all 20 candidate stocks + cash). The engine fetches and tracks all of them throughout the backtest.
- `get_target_weights()` at each rebalance:
  1. Uses `prices_history` (from context) to compute rolling OLS beta for each universe stock vs SPY
  2. Ranks by beta; picks bottom-N as long book, top-N as short book
  3. Scales book sizes so `avg_beta_long × long_book_size ≈ avg_beta_short × short_book_size` for true beta neutrality
  4. Allocates equal weight within each book, cash absorbs residual

The SPY benchmark is passed as a pre-loaded DataFrame at construction (`benchmark_prices`) so no live fetch occurs inside `get_target_weights`, matching the `BetaNeutral` pattern.

Beta neutrality for N-symbol case (better than equal-weight in `BetaNeutral`):
```
long_book_size  = book_size
short_book_size = book_size × (avg_beta_long / avg_beta_short)  [clamped: min 0.1, max 2.0]
w_long_i  = long_book_size / n_long    (equal within book)
w_short_j = -short_book_size / n_short (equal within book)
cash      = 1.0 - net
```
This ensures `Σ w_i × β_i ≈ 0` even when the two books have different average betas.

**3. Universe for BetaNeutral notebook**

A 20-stock universe covering the beta spectrum, chosen to be stable, liquid, and cover multiple sectors:

- **Low beta** (potential longs): JNJ, PG, KO, WMT, VZ, ED, MCD, PEP
- **High beta** (potential shorts): NVDA, AMD, META, TSLA, MELI, PLTR, COIN, SMCI
- **Mid** (rotates between books): MSFT, AAPL, AMZN, GOOGL
- **Cash**: BIL

`get_symbols()` returns all 20 + BIL (21 total). The engine fetches and tracks them all.

**4. Data sourcing — YFinance with disk cache**

All notebooks follow the existing pattern:
```python
from tiportfolio.helpers.cache import enable_data_source_cache
from tiportfolio.helpers.data import YFinance
enable_data_source_cache("tiportfolio", cache_dir=".cache")
yf = YFinance(auto_adjust=True)
df = yf.query(SYMBOLS, start_date=START, end_date=END)
```

SPY benchmark is fetched once separately and stored as a DataFrame for `BetaScreenerStrategy`.

**5. Comparison strategy for each notebook**

| Notebook | Strategy | Baselines |
|---|---|---|
| DollarNeutral | TXN long / KVUE short (1:1.135) | Long TXN only; Short KVUE only; Fixed 50/50 TXN+BIL |
| VolatilityTargeting | Inverse-vol QQQ/BIL/GLD | Fixed 70/20/10; Long QQQ only |
| BetaNeutral | 5-long / 5-short dynamic | Long SPY; Fixed equal-weight universe |

**6. Utility location**

`src/tiportfolio/utils/beta_screener.py` — contains `BetaScreenerStrategy` class, exported from `src/tiportfolio/__init__.py`. Notebooks import it as `from tiportfolio import BetaScreenerStrategy`. This keeps all strategy-level code inside the installed package, consistent with existing utility modules in `src/tiportfolio/utils/`.

## Risks / Trade-offs

- [Risk] 20-stock YFinance fetch may be slow on first run → Mitigation: disk cache ensures subsequent runs are fast; notebook documents this
- [Risk] Some universe stocks may have missing data for early history → Mitigation: `merge_prices` uses `how="inner"` by default, so only dates with full coverage are used
- [Risk] `BetaScreenerStrategy` in notebooks/utils is not tested by the main test suite → Mitigation: notebook itself serves as integration test; add a doctest or simple assertion in the utility
- [Risk] Short positions in a long-only broker context → Mitigation: notebooks include a disclaimer cell that BetaNeutral and DollarNeutral require a margin account
- [Trade-off] Equal-weight-within-book for screener (not optimal convex combination) is a deliberate simplification; produces a clean, interpretable notebook
- [Trade-off] `long_book_size` / `short_book_size` override `book_size` per side but the tolerance-band imbalance check uses the per-side targets, which adds a small amount of extra code complexity — accepted as the asymmetric ratio is a core notebook requirement
