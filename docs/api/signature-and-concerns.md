# API Signature Review & Concerns

Review of `docs/api/index.md` and `docs/guides/` — inconsistencies, gaps, and signature design issues.

---

## 1. Inconsistencies

### A. Stack diagram label mismatch (`index.md`)
The second row of the namespace diagram says `Schedule.*` but the namespace was renamed to `Signal.*`.

### B. `key-data-types.md` uses old class name
The context contract table says `VixSignal (and other signal algos)`. Should be `Signal.VIX`.

### C. Parent portfolio `Action.Rebalance()` inconsistency
The VIX parent stack has no `Action.Rebalance()`. The dollar-neutral parent does. If the engine routes capital automatically after a signal algo sets `selected_child`, then dollar-neutral's `Action.Rebalance()` is redundant. If it's required to actually move capital, the VIX guide is missing it. **Needs resolution — see open questions.**

### D. `plot()` references benchmark but `TiConfig` has none
`index.md` states "Equity curve vs benchmark (default: SPY)". Benchmark was removed from `TiConfig` and there is no parameter on `plot()` to set it. The feature is mentioned but has no API entry point.

### E. `lag` type mismatch in `Select.Momentum`
API table shows `lag=1` (int). Guide examples use `lag=pd.DateOffset(days=1)`. Type must be consistent.

### F. `summary()` return type annotation incomplete
Signature shows `-> dict[str, float]` but for multiple backtests it returns `pd.DataFrame`. **Needs resolution — see open questions.**

---

## 2. Missing Documentation

| Gap | Detail |
|---|---|
| Data caching | `enable_data_source_cache()` in `helpers/cache.py` is not mentioned anywhere in the public API |
| `Context` fields | Custom algo section shows `context.date` but never lists all fields available (`.prices`, `.config`, `.selected`, `.weights`, `.selected_child`, `.portfolio`) |
| `Algo` / `Context` import path | Extending section imports from `tiportfolio.algo` (internal module). Should these be importable directly from `tiportfolio`? |
| `branching` guide | `Or`, `And`, `Not` are defined but no guide shows a real composed use case |
| `Signal.VIX` split-capital | Only example routes 100% to one child. Split-capital (e.g., 70/30 across both children) is undocumented |
| `BacktestResult.trades` for tree portfolios | Shape of the trades DataFrame when parent/child portfolios are involved is not documented |

---

## 3. Workflow / Design Issues

### Parent portfolio `Action.Rebalance()` — Open Question
Two examples contradict each other:
- VIX example: parent has no `Action.Rebalance()`
- Dollar-neutral: parent has `Action.Rebalance()`

**Options:**
- **Explicit always**: require `Action.Rebalance()` in parent stacks — consistent with leaf portfolios; makes capital routing visible
- **Implicit for child-routing**: engine handles capital routing to `selected_child` automatically; `Action.Rebalance()` only needed when parent itself holds tickers

Recommendation: explicit always. The user should see `Action.Rebalance()` in every stack that moves capital — it makes the intent clear and avoids magic behaviour.

### `Select.Momentum` proxy description doesn't fit
All other proxies compute their value then delegate to a base (`Weigh.Equally` → `Weigh.Weigh`, `Signal.Monthly` → `Signal.Schedule`). `Select.Momentum` is described as "proxy → `Select.Select`", but the momentum computation IS the selection — it doesn't pre-compute then hand off to a base. The proxy framing is misleading here. `Select.Momentum` should be described as a direct implementation of `Select.Select`, not a proxy.

### `Signal.VIX` initial state undocumented
The hysteresis note says "previous selection persists" when VIX is between thresholds. On the very first evaluation there is no previous selection. What is selected by default? This edge case is unspecified.

### `Weigh.Weigh` vs `Weigh.Ratio` — when to use which?
Both take `dict[str, float]`. The difference is normalisation. A user with `{"QQQ": 0.7, "BIL": 0.3}` (already sums to 1.0) doesn't know which to use. `Weigh.Weigh` is also a confusing name for a class users would call directly — the double word reads awkwardly.

---

## 4. Signature Review

### `fetch_data`
```python
ti.fetch_data(
    tickers: list[str],
    start: str,                          # "YYYY-MM-DD"
    end: str,                            # "YYYY-MM-DD"
    source: str = "yfinance",            # "yfinance" | "alpaca"
    cache: bool = False,                 # missing — enable disk caching
) -> pd.DataFrame
```

### `Signal.VIX`
```python
Signal.VIX(
    high: float,
    low: float,
    data: pd.DataFrame,    # was `signal` — conflicts with Signal namespace name
) -> bool
```

### `Select.Momentum`
```python
Select.Momentum(
    n: int,
    lookback: pd.DateOffset,
    lag: pd.DateOffset = pd.DateOffset(days=1),   # was int; must be DateOffset
    sort_descending: bool = True,
) -> bool
```

### `Weigh.Equally` — open question
```python
# Current:
Weigh.Equally(sign: int = 1) -> bool     # sign=-1 for short; not obvious

# Option A:
Weigh.Equally(short: bool = False) -> bool

# Option B:
Weigh.Equally(direction: Literal["long", "short"] = "long") -> bool
```
See open questions below.

### `Weigh.BasedOnHV` / `Weigh.BasedOnBeta` — add type annotations
```python
Weigh.BasedOnHV(
    initial_ratio: dict[str, float],
    target_hv: float,            # annualised volatility target (e.g. 60 = 60%)
    lookback: pd.DateOffset,
) -> bool

Weigh.BasedOnBeta(
    initial_ratio: dict[str, float],
    target_beta: float,
    lookback: pd.DateOffset,
) -> bool
```

### `Weigh.ERC` — add type annotation for lookback
```python
Weigh.ERC(
    lookback: pd.DateOffset,
    covar_method: str = "ledoit-wolf",
    risk_parity_method: str = "ccd",
    maximum_iterations: int = 100,
    tolerance: float = 1e-8,
) -> bool
```

### `BacktestResult`
```python
result.summary() -> dict[str, float] | pd.DataFrame    # currently only shows dict
result.full_summary() -> dict[str, float] | pd.DataFrame
result.plot(interactive: bool = True) -> None           # benchmark: see open questions
result.plot_histogram(interactive: bool = True) -> None
result.plot_security_weights(interactive: bool = True) -> None
```

---

## Open Questions

### Q1 — `summary()` return type
Currently `-> dict[str, float]`. For multiple backtests, returns `pd.DataFrame`.

Options:
- **Union type** `dict | DataFrame` — honest but means callers must type-check
- **Always DataFrame** — consistent; single backtest returns a one-column DataFrame; breaks simple dict access like `result.summary()["cagr"]`
- **Custom `Summary` object** — supports both `summary["cagr"]` and `summary.to_frame()`; adds a new type to the public API

### Q2 — `Weigh.Equally` short parameter
`sign=-1` works but reads like internal implementation detail.

Options:
- `short: bool = False` — simplest, clear intent
- `direction: Literal["long", "short"] = "long"` — more explicit, extensible

### Q3 — `Action.Rebalance()` in parent portfolios
Should parent portfolios always include `Action.Rebalance()` explicitly, or is capital routing to `selected_child` handled implicitly by the engine?

Recommendation: require it explicitly. Implicit routing is surprising; explicit Rebalance makes the stack self-documenting.
