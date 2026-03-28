# TiPortfolio Core Engine Implementation Design

**Date:** 2026-03-28
**Status:** Approved
**Branch:** simplify
**Preceding spec:** `2026-03-26-library-structure-design.md`

---

## Scope

This spec covers the full implementation of the TiPortfolio core engine as described in `docs/api/index.md` and `docs/guides/`. The preceding spec established file layout and naming. This spec defines internal contracts, data flow, simulation loop, algo catalogue, results layer, and resolves all gaps found during design review.

---

## Gaps Resolved (vs current docs)

| # | Gap | Resolution |
|---|-----|------------|
| 1 | `fetch_data` in `api/index.md` declares `-> pd.DataFrame`; `context.prices` description is also wrong | Return type is `dict[str, pd.DataFrame]`. `context.prices` is the full dict (all history), not sliced. Both descriptions must be corrected in `api/index.md`. |
| 2 | `Select.Filter` documented in `extra-data.md` but missing from `api/index.md` Select table | Add to `api/index.md` and implement in `algos/select.py`. Must be added to docs **before** implementation. |
| 3 | `ti.validate_data()` in `extra-data.md` but not in API reference | Add to public API and add usage example to `extra-data.md`. |
| 4 | Short selling: `Weigh.Equally(short=True)` used but engine mechanics unspecified | Negative weights in `context.weights`; daily borrow costs; negative `positions` qty. |
| 5 | `Weigh.BasedOnBeta` needs a benchmark ticker to compute beta | Add `benchmark_ticker: str = "SPY"` as a constructor parameter on `Weigh.BasedOnBeta` — not on `TiConfig`. |
| 6 | `result.trades.sample(10)` described as top/bottom trades but pandas `.sample()` is random | Custom `Trades` wrapper with `.sample(n)` returning top/bottom n by equity return. Add to `api/index.md`. |
| 7 | `context.prices` described as "sliced to current date" — ambiguous for lookback algos | Full history dict passed; each algo slices to its own lookback window. |
| 8 | `Signal.Quarterly` shown as expanding to `Or(...)` — unclear if factory or class | `Algo` subclass composing `Or` in `__init__`, exposes clean `__call__`. |
| 9 | No spec for cash state before first rebalance | `cash = initial_capital`, `positions = {}` until first rebalance fires. |
| 10 | `BacktestResult` — unclear if `result[0]` works for single backtest | `BacktestResult` always a collection; `result[0]` and `result["name"]` always work. |
| 11 | `market-volatility-rebalance.md` references `context.selected_child` which no longer exists | Guide updated: `Signal.VIX` writes to `context.selected` and `context.weights` directly. |
| 12 | `allocation-strategies.md` volatility targeting snippet missing `import pandas as pd` | Fix added. |

---

## 1. Data Layer

### `fetch_data`

```python
def fetch_data(
    tickers: list[str],
    start: str,
    end: str,
    source: str = "yfinance",    # "yfinance" | "alpaca"
) -> dict[str, pd.DataFrame]:
```

- **Key**: ticker string (`"QQQ"`, `"^VIX"`, `"SPY"`)
- **Value**: `pd.DataFrame` with `DatetimeIndex` (UTC), columns `open`, `high`, `low`, `close`, `volume`
- Normalises all timestamps to UTC; forward-fills calendar gaps using `pandas-market-calendars`
- Caching behaviour unchanged from existing `helpers/data.py`

The existing helpers return per-ticker DataFrames natively. `fetch_data` is a thin wrapper that collects them into a dict and normalises timestamps.

### `ti.validate_data()`

```python
def validate_data(
    data: dict[str, pd.DataFrame],
    extra: dict[str, pd.DataFrame] | None = None,
) -> None:
```

Checks all DataFrames in `data` (and optionally `extra`) share identical `DatetimeIndex` values. Raises `ValueError` with the first misaligned date and the ticker names involved. Called automatically by the engine at `Backtest` construction; also callable by users before running.

### `Backtest` constructor — corrected data type

```python
ti.Backtest(
    portfolio: Portfolio,
    data: dict[str, pd.DataFrame],    # NOT pd.DataFrame — fix api/index.md
    fee_per_share: float | None = None,
    config: TiConfig | None = None,
)
```

---

## 2. Core Abstractions (`algo.py`)

### `Context`

Passed to every `Algo.__call__`. Carries read-only inputs and mutable inter-algo communication. Also carries engine callbacks so `Action.Rebalance` can trigger execution without importing `backtest.py` (avoids circular imports).

```python
@dataclass
class Context:
    # read-only inputs
    portfolio: Portfolio
    prices: dict[str, pd.DataFrame]    # full price history, all tickers; algos slice themselves
    date: pd.Timestamp                 # current evaluation date
    config: TiConfig

    # mutable inter-algo communication
    selected: list[str | Portfolio] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)
    # key = ticker string or portfolio.name; negative value = short position

    # engine callbacks — set by engine before calling algo_queue (not by user code)
    _execute_leaf: Callable[[Portfolio, Context], None] | None = field(default=None, repr=False)
    _allocate_children: Callable[[Portfolio, Context], None] | None = field(default=None, repr=False)
```

**`selected_child` is not a field.** `Signal.VIX` writes `context.selected = [chosen_child]` and `context.weights = {chosen_child.name: 1.0}`, so `Action.Rebalance` handles regime-switching parent nodes identically to any other parent — no special-casing in the engine.

Portfolio state (positions, cash, equity) lives on `Portfolio` itself, not on `Context`. Algos needing current positions read `context.portfolio.positions`.

**`AlgoQueue` short-circuit note:** `AlgoQueue` uses `all(algo(context) for algo in self.algos)` which short-circuits on the first `False`. Algos after a `False` return do **not** run — `context.selected` and `context.weights` remain at their initial empty values. Downstream algos (Weigh, Rebalance) must not assume these fields are populated unless a Select algo ran successfully.

### `Algo`

```python
class Algo(ABC):
    @abstractmethod
    def __call__(self, context: Context) -> bool:
        """Return True to continue the AlgoQueue, False to abort."""
```

All signal, select, weigh, and action classes are `Algo` subclasses. No factories, no static methods that return non-`Algo` types.

### `AlgoQueue`

```python
class AlgoQueue(Algo):
    def __init__(self, algos: list[Algo]) -> None: ...
    def __call__(self, context: Context) -> bool:
        return all(algo(context) for algo in self.algos)
```

Sequential AND — stops on first `False`. `Portfolio.__init__` wraps its `algos` list in an `AlgoQueue` automatically.

### Branching combinators

Defined in `algo.py`; re-exported as `ti.Or`, `ti.And`, `ti.Not` via `branching.py`.

```python
class Or(Algo):
    """Returns True when any inner algo returns True (short-circuits on first True)."""
    def __init__(self, *algos: Algo) -> None: ...

class And(Algo):
    """Returns True only when all inner algos return True. Explicit nestable AlgoQueue."""
    def __init__(self, *algos: Algo) -> None: ...

class Not(Algo):
    """Returns True when the wrapped algo returns False."""
    def __init__(self, algo: Algo) -> None: ...
```

---

## 3. Portfolio State

```python
class Portfolio:
    name: str
    algo_queue: AlgoQueue                               # built from user's algos list
    children: list[str] | list[Portfolio] | None

    # mutable state — updated by engine on every bar
    positions: dict[str, float]    # ticker → qty held; negative = short; always {} for parent nodes
    cash: float                    # always 0.0 for parent nodes; leaf nodes track uninvested cash
    equity: float                  # leaf: cash + sum(qty*price); parent: sum(child.equity)
```

**Parent vs leaf node distinction:**
- **Leaf node**: `children` is `list[str]` or `None`. Tracks `positions` and `cash` directly. `equity = cash + sum(pos * price)`.
- **Parent node**: `children` is `list[Portfolio]`. Never holds direct market positions — `positions = {}`, `cash = 0.0` always. `equity = sum(child.equity for child in children)`.

Initial state at engine start: `positions = {}`, `cash = config.initial_capital` (leaf) or `0.0` (parent), `equity = config.initial_capital`.

---

## 4. Simulation Engine (`backtest.py`)

### Loop structure

```
trading_days = sorted union of DatetimeIndex values across all tickers in prices

for date in trading_days:
    mark_to_market(root_portfolio, prices, date)       # updates .equity on all nodes
    deduct_daily_carry_costs(root_portfolio, prices, date, config)
    record_equity(root_portfolio, date)                # appends (date, equity) to equity curve

    context = Context(
        portfolio=root_portfolio,
        prices=prices,
        date=date,
        config=config,
        _execute_leaf=execute_leaf_trades,
        _allocate_children=allocate_equity_to_children,
    )
    evaluate_node(root_portfolio, context)
```

### Node evaluation (recursive)

```
evaluate_node(portfolio, context):

  # Pre-seed context.selected with all children. Select algos (e.g. Select.Momentum)
  # read this as their input universe and overwrite it with their filtered subset.
  # Do NOT remove this pre-seed — Select.Momentum depends on it.
  is_parent = (
      portfolio.children is not None
      and len(portfolio.children) > 0
      and isinstance(portfolio.children[0], Portfolio)
  )
  context.selected = list(portfolio.children or [])

  # Run the algo queue. Action.Rebalance inside the queue fires _execute_leaf (leaf)
  # or _allocate_children (parent). Do NOT call those callbacks again here — that
  # would cause double execution on every rebalance.
  portfolio.algo_queue(context)

  # For parent nodes only: recurse into each child that the queue selected.
  # context.selected may be a subset (e.g. Signal.VIX picks one child regime).
  if is_parent:
      for child in context.selected:
          child_context = Context(
              portfolio=child,
              prices=context.prices,    # propagate from parent context, not bare variable
              date=context.date,        # propagate from parent context, not bare variable
              config=context.config,
              _execute_leaf=execute_leaf_trades,
              _allocate_children=allocate_equity_to_children,
          )
          evaluate_node(child, child_context)
```

Node type is determined at evaluation time by inspecting `portfolio.children`. No type flag is stored on `Portfolio`.

### Leaf trade execution (`execute_leaf_trades`)

Computes delta between current positions and target, executes at closing price:

```
for ticker in context.selected:
    target_weight = context.weights.get(ticker, 0.0)   # negative for short
    target_value  = portfolio.equity * target_weight
    price         = prices[ticker].loc[date, "close"]
    current_qty   = portfolio.positions.get(ticker, 0.0)
    current_value = current_qty * price
    delta_value   = target_value - current_value
    delta_qty     = delta_value / price                 # fractional shares allowed

    fee = abs(delta_qty) * config.fee_per_share
    portfolio.positions[ticker] = current_qty + delta_qty
    portfolio.cash -= delta_qty * price + fee
    # selling or shorting (delta_qty < 0) → cash increases

# close positions for tickers in portfolio.positions but absent from context.selected
for ticker in list(portfolio.positions):
    if ticker not in context.selected:
        price    = prices[ticker].loc[date, "close"]
        qty      = portfolio.positions[ticker]
        fee      = abs(qty) * config.fee_per_share
        portfolio.cash += qty * price - fee
        del portfolio.positions[ticker]
```

### Parent equity allocation (`allocate_equity_to_children`)

Does not execute market orders. Sets each selected child's equity budget:

```
selected_names = {c.name for c in context.selected}

# Step 1: Liquidate deselected children and update their equity to the recovered proceeds.
# Do NOT absorb into portfolio.cash — parent nodes always have cash=0.0.
# Instead, temporarily store recovered value in child.equity so it is included in the
# total available capital computed below.
for child in portfolio.children:
    if child.name not in selected_names and child.positions:
        _liquidate_child(child, context.prices, context.date, context.config)
        child.equity = child.cash   # recovered proceeds net of fees
        child.cash   = 0.0

# Step 2: Total available capital = sum of all children's equity.
# Selected children contribute their current marked-to-market equity.
# Deselected (just liquidated) children contribute their recovered proceeds.
# This correctly accounts for liquidation fees without touching portfolio.cash.
total_equity = sum(c.equity for c in portfolio.children)

# Step 3: Redistribute to selected children.
# Use .get() with a 0.0 default: if Weigh.Ratio omits a child's name, that child
# receives no equity (equivalent to being deselected). This prevents a KeyError.
for child in context.selected:
    fraction     = context.weights.get(child.name, 0.0)
    child.equity = total_equity * fraction
    # child.cash is NOT overwritten — reconciled on the child's next trade execution

# Step 4: Zero deselected children completely.
for child in portfolio.children:
    if child.name not in selected_names:
        child.equity = 0.0
        child.cash   = 0.0
```

### Child liquidation (`_liquidate_child`)

```
# Signature: _liquidate_child(child, prices, date, config)
for ticker, qty in list(child.positions.items()):
    price = prices[ticker].loc[date, "close"]
    fee   = abs(qty) * config.fee_per_share
    child.cash += qty * price - fee
    del child.positions[ticker]
# child.positions is now {}; child.cash holds all recovered proceeds (net of fees)
```

After `_liquidate_child`, the caller sets `child.equity = child.cash` to surface the recovered value for total-capital computation, then zeros `child.cash`. The child is ready to receive a fresh equity allocation. The parent's `cash` is never modified — parent nodes always have `cash = 0.0`.

### Mark-to-market

Run on every bar before algo evaluation:

```
def mark_to_market(portfolio, prices, date):
    if is_leaf(portfolio):
        portfolio.equity = portfolio.cash + sum(
            qty * prices[ticker].loc[date, "close"]
            for ticker, qty in portfolio.positions.items()
        )
    else:  # parent node
        for child in portfolio.children:
            mark_to_market(child, prices, date)
        portfolio.equity = sum(child.equity for child in portfolio.children)
        # parent.cash and parent.positions are always 0/{} — not included
```

### Daily carry costs (run every bar, after mark-to-market, before algo evaluation)

Only applies to leaf nodes:

```
def deduct_daily_carry_costs(portfolio, prices, date, config):
    if is_parent(portfolio):
        for child in portfolio.children:
            deduct_daily_carry_costs(child, prices, date, config)
        return

    for ticker, qty in portfolio.positions.items():
        if qty == 0.0:
            continue
        price = prices[ticker].loc[date, "close"]

        # short borrow cost
        if qty < 0:
            portfolio.cash -= abs(qty * price) * config.stock_borrow_rate / config.bars_per_year

    # leverage cost: when total long market value exceeds portfolio equity
    long_value = sum(
        qty * prices[t].loc[date, "close"]
        for t, qty in portfolio.positions.items()
        if qty > 0
    )
    if long_value > portfolio.equity:
        portfolio.cash -= (long_value - portfolio.equity) * config.loan_rate / config.bars_per_year
```

---

## 5. Algo Catalogue

### Signal algos (`algos/signal.py`)

All are `Algo` subclasses.

**`Signal.Schedule`** — base time-based trigger:

```python
class Schedule(Algo):
    def __init__(
        self,
        month: int | None = None,        # None = every month; 1-12 = specific month only
        day: int | str = "end",          # "end" | "start" | day-of-month int
        next_trading_day: bool = True,
    ) -> None: ...
    def __call__(self, context: Context) -> bool: ...
```

Uses `pandas_market_calendars` (NYSE calendar by default) to resolve actual trading days. Returns `True` only when `context.date` matches the scheduled date.

**`Signal.Monthly`** — delegates to `Schedule`:

```python
class Monthly(Algo):
    def __init__(self, day: int | str = "end", next_trading_day: bool = True) -> None:
        self._inner = Signal.Schedule(day=day, next_trading_day=next_trading_day)
    def __call__(self, context: Context) -> bool:
        return self._inner(context)
```

**`Signal.Quarterly`** — delegates to `Or(Schedule(...), ...)`:

```python
class Quarterly(Algo):
    def __init__(self, months: list[int] = [2, 5, 8, 11], day: str = "end") -> None:
        self._inner = Or(*[Signal.Schedule(month=m, day=day) for m in months])
    def __call__(self, context: Context) -> bool:
        return self._inner(context)
```

**`Signal.VIX`** — regime-switching; writes to `context.selected` and `context.weights`:

```python
class VIX(Algo):
    def __init__(
        self,
        high: float,
        low: float,
        data: dict[str, pd.DataFrame],   # must contain "^VIX"
    ) -> None:
        self._high = high
        self._low = low
        self._data = data
        self._active: Portfolio | None = None   # lazily initialized on first call
```

**Children ordering contract (required invariant):**
- `portfolio.children[0]` = portfolio activated when VIX < `low` (low-vol / risk-on regime)
- `portfolio.children[1]` = portfolio activated when VIX > `high` (high-vol / risk-off regime)

This must match the order in which child portfolios are passed to the parent `Portfolio` constructor. The guide example shows `[low_vol_portfolio, high_vol_portfolio]` — this is the required ordering.

```python
    def __call__(self, context: Context) -> bool:
        # lazy initialization: default to low-vol regime (children[0])
        if self._active is None:
            self._active = context.portfolio.children[0]

        vix_now = self._data["^VIX"].loc[context.date, "close"]
        if vix_now > self._high:
            self._active = context.portfolio.children[1]
        elif vix_now < self._low:
            self._active = context.portfolio.children[0]
        # else: between thresholds — hysteresis, keep self._active unchanged

        context.selected = [self._active]
        context.weights = {self._active.name: 1.0}
        return True
```

---

### Select algos (`algos/select.py`)

**`Select.All`** — copies `portfolio.children` into `context.selected`:

```python
class All(Algo):
    def __call__(self, context: Context) -> bool:
        context.selected = list(context.portfolio.children or [])
        return True
```

Works for both `list[str]` (leaf tickers) and `list[Portfolio]` (parent children).

**`Select.Momentum`** — selects top/bottom `n` tickers by return over lookback:

```python
class Momentum(Algo):
    def __init__(
        self,
        n: int,
        lookback: pd.DateOffset,
        lag: pd.DateOffset = pd.DateOffset(days=1),
        sort_descending: bool = True,
    ) -> None: ...
    def __call__(self, context: Context) -> bool:
        end = context.date - self.lag
        start = end - self.lookback
        scores = {
            t: context.prices[t].loc[start:end, "close"].pct_change().sum()
            for t in context.selected
            if isinstance(t, str)   # only operates on ticker strings
        }
        ranked = sorted(scores, key=scores.get, reverse=self.sort_descending)
        context.selected = ranked[:self.n]
        return True
```

**`Select.Filter`** — boolean gate using external data series; returns `False` to halt the queue without modifying `context.selected`:

```python
class Filter(Algo):
    def __init__(
        self,
        data: dict[str, pd.DataFrame],
        condition: Callable[[dict[str, pd.Series]], bool],
    ) -> None: ...
    def __call__(self, context: Context) -> bool:
        row = {ticker: df.loc[context.date] for ticker, df in self.data.items()}
        passed = self.condition(row)
        # False → queue halts, portfolio holds previous positions (no rebalance)
        # True  → queue continues; context.selected is unchanged
        return passed
```

---

### Weigh algos (`algos/weigh.py`)

All read `context.selected`, write `context.weights`. Keys in `context.weights` are always strings (ticker or `portfolio.name`).

**`Weigh.Equally`:**

```python
class Equally(Algo):
    def __init__(self, short: bool = False) -> None: ...
    def __call__(self, context: Context) -> bool:
        n = len(context.selected)
        sign = -1.0 if self.short else 1.0
        context.weights = {
            (item if isinstance(item, str) else item.name): sign / n
            for item in context.selected
        }
        return True
```

**`Weigh.Ratio`** — explicit weights, normalised to sum of absolute values = 1.0 (full investment):

```python
class Ratio(Algo):
    def __init__(self, weights: dict[str, float]) -> None: ...
    def __call__(self, context: Context) -> bool:
        keys = [i if isinstance(i, str) else i.name for i in context.selected]
        raw = {k: self.weights[k] for k in keys if k in self.weights}
        total = sum(abs(v) for v in raw.values()) or 1.0
        context.weights = {k: v / total for k, v in raw.items()}
        # Note: always fully invested — weights normalise to sum(|w|) = 1.
        # Weights not in self.weights for selected items are treated as 0 (position closed).
        return True
```

**`Weigh.BasedOnHV`** — volatility targeting; scales `initial_ratio` to match `target_hv`:

> **Unit:** `target_hv` is expressed as an **annualised decimal** (e.g., `0.15` = 15% vol, `0.60` = 60% vol). The algorithm computes HV in the same decimal space via `std * sqrt(bars_per_year)`. Passing a percentage integer (e.g., `60`) instead of a decimal (e.g., `0.60`) will silently apply ~300x leverage.

Algorithm:
1. Compute annualised historical volatility for each selected ticker over `lookback`:
   ```
   hv_t = daily_returns_t.std() * sqrt(bars_per_year)   # e.g. 0.20 for 20% annual vol
   ```
2. Start from `initial_ratio` weights `w`.
3. Approximate portfolio HV (diagonal covariance, ignores cross-asset correlation):
   ```
   portfolio_hv = sqrt(sum((w_t * hv_t) ** 2 for t in selected))
   ```
4. Scale factor: `scale = target_hv / portfolio_hv` (if `portfolio_hv > 0`)
5. Scaled weights: `w_scaled_t = w_t * scale` for all `t`.
6. Weights are **not** normalised to sum to 1 — the scale factor represents leverage (>1) or de-leverage (<1). The cash residual when `sum(w) < 1` remains in `portfolio.cash`.

**`Weigh.BasedOnBeta`** — beta-neutral; adjusts `initial_ratio` so portfolio beta → `target_beta`:

Accepts `benchmark_ticker: str = "SPY"` as a constructor parameter. The benchmark ticker must be present in `context.prices` (i.e., included in the `data` dict passed to `Backtest`). If the ticker is absent from `context.prices`, raises `KeyError` at call time.

Algorithm:
1. Compute benchmark daily returns over `lookback`:
   ```
   r_bench = prices[self._benchmark_ticker].loc[start:end, "close"].pct_change().dropna()
   ```
2. Compute beta for each selected ticker:
   ```
   beta_t = cov(r_t, r_bench) / var(r_bench)
   ```
3. Compute initial portfolio beta: `beta_port = sum(w_t * beta_t)` using `initial_ratio`.
4. Iteratively adjust weights toward `target_beta` using proportional scaling:
   - If `beta_port ≈ target_beta` (within 1e-6): return `initial_ratio` as is.
   - Otherwise: shift weight from the highest-beta ticker to the lowest-beta ticker in proportion to their beta distance from `target_beta`, repeating until convergence (max 1000 iterations, tolerance 1e-6).
5. Weights may become negative (short) if `target_beta` requires it.
6. Result is **not** normalised to sum to 1 — consistent with `BasedOnHV`.

**`Weigh.ERC`** — equal risk contribution (risk parity); delegates to `riskfolio-lib`:

Constructor: `(lookback: pd.DateOffset, covar_method: str = "ledoit-wolf", risk_parity_method: str = "ccd", maximum_iterations: int = 100, tolerance: float = 1e-8)`

- Builds full covariance matrix over `lookback`
- `covar_method`: `"ledoit-wolf"` (default) | `"hist"` | `"oas"`
- `risk_parity_method`: `"ccd"` (default) | `"slsqp"`
- `maximum_iterations` / `tolerance`: passed through to the riskfolio-lib solver
- Weights always sum to 1.0 (fully invested, long-only)

---

### Action algos (`algos/rebalance.py`)

**`Action.Rebalance`** — execution algo; uses engine callbacks from `Context`:

```python
class Rebalance(Algo):
    def __call__(self, context: Context) -> bool:
        children = context.portfolio.children
        is_parent = (
            children is not None
            and len(children) > 0
            and isinstance(children[0], Portfolio)
        )
        if is_parent:
            context._allocate_children(context.portfolio, context)
        else:
            context._execute_leaf(context.portfolio, context)
        return True
```

Callbacks are injected by the engine when creating `Context` at the start of each evaluation. `Action.Rebalance` never imports from `backtest.py` — the circular import is avoided entirely.

**`Action.PrintInfo`** — debug; always returns `True`:

```python
class PrintInfo(Algo):
    def __call__(self, context: Context) -> bool:
        print(f"[{context.date.date()}] portfolio={context.portfolio.name}")
        print(f"  equity={context.portfolio.equity:.2f}  cash={context.portfolio.cash:.2f}")
        print(f"  positions={context.portfolio.positions}")
        print(f"  selected={[i if isinstance(i, str) else i.name for i in context.selected]}")
        print(f"  weights={context.weights}")
        return True
```

---

## 6. Results Layer

### Equity curve

The engine records `portfolio.equity` on **every bar** (not just rebalance days) into an internal `list[tuple[pd.Timestamp, float]]`. This produces a smooth daily series for charting and metric computation. Only the root portfolio's equity curve is recorded; child portfolios do not generate separate curves (the root curve captures the full portfolio value).

### `Trades` wrapper

`Trades` wraps a `pd.DataFrame` without subclassing (subclassing pandas is fragile across versions):

```python
class Trades:
    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    def __getattr__(self, name: str) -> Any:
        return getattr(self._df, name)    # delegates all pandas operations transparently

    def __getitem__(self, key: Any) -> Any:
        return self._df[key]

    def __repr__(self) -> str:
        return repr(self._df)

    def sample(self, n: int) -> pd.DataFrame:
        """Returns the top n and bottom n rebalances by equity return.

        If fewer than n rebalances exist, returns all available in each direction.
        Result contains at most 2n rows; rows that appear in both top-n and bottom-n
        (only possible when n >= len(r)) are deduplicated.
        """
        r = self._df["equity_after"] / self._df["equity_before"] - 1
        top    = self._df.loc[r.nlargest(min(n, len(r))).index]
        bottom = self._df.loc[r.nsmallest(min(n, len(r))).index]
        return pd.concat([top, bottom]).loc[lambda df: ~df.index.duplicated()].sort_index()
```

Trade record columns (one row per rebalance event per leaf node):

| Column | Description |
|---|---|
| `date` | Rebalance date |
| `equity_before` | Leaf portfolio equity before trades |
| `equity_after` | Leaf portfolio equity after trades and fees |
| `fee_paid` | Total fee for this rebalance event |
| `{TICKER}_price` | Closing price at execution |
| `{TICKER}_qty_before` | Shares held before (negative = short) |
| `{TICKER}_trade_qty` | Shares bought (+) or sold/shorted (−) |
| `{TICKER}_qty_after` | Shares held after (negative = short) |
| `{TICKER}_value_after` | Position value after (negative for short) |

### `_SingleResult`

```python
class _SingleResult:
    portfolio_name: str
    trades: Trades
    _equity_curve: pd.Series    # DatetimeIndex → float, daily, root portfolio only
    _config: TiConfig

    def summary(self) -> pd.DataFrame: ...
    def full_summary(self) -> pd.DataFrame: ...
    def plot(self, interactive: bool = True) -> None: ...
    def plot_histogram(self, interactive: bool = True) -> None: ...
    def plot_security_weights(self, interactive: bool = True) -> None: ...
```

### `BacktestResult`

Always a collection — single and multi-backtest usage are identical:

```python
class BacktestResult:
    _results: list[_SingleResult]
    _name_to_idx: dict[str, int]

    def __getitem__(self, key: int | str) -> _SingleResult: ...

    def summary(self) -> pd.DataFrame: ...          # rows=metrics, cols=portfolio names
    def full_summary(self) -> pd.DataFrame: ...
    def plot(self, interactive: bool = True) -> None: ...
    def plot_histogram(self, interactive: bool = True) -> None: ...
    def plot_security_weights(self, interactive: bool = True) -> None: ...
```

### Metrics (from `_equity_curve`)

```
daily_returns  = equity_curve.pct_change().dropna()
excess_returns = daily_returns - config.risk_free_rate / config.bars_per_year

cagr       = (final / initial) ** (bars_per_year / n_bars) - 1
sharpe     = excess_returns.mean() / excess_returns.std() * sqrt(bars_per_year)
sortino    = excess_returns.mean() / excess_returns[excess_returns < 0].std() * sqrt(bars_per_year)
max_dd     = (equity_curve / equity_curve.cummax() - 1).min()
calmar     = cagr / abs(max_dd)
kelly      = excess_returns.mean() / excess_returns.var()
```

Period returns (MTD, YTD, 1Y, 3Y, 5Y, 10Y, inception) are sliced from `_equity_curve` using `pd.DateOffset`. Monthly and yearly aggregations resampled from daily returns.

### Charting architecture

Shared data preparation; two rendering backends selected per call:

```
_SingleResult._prepare_equity_data()       → pd.DataFrame (equity + drawdown columns)
_SingleResult._prepare_histogram_data()    → pd.Series (daily returns)
_SingleResult._prepare_weights_data()      → pd.DataFrame (date × ticker, from trades)
                    ↓
_render_plotly(data)        ← interactive=True   (Plotly, already in dev deps)
_render_matplotlib(data)    ← interactive=False  (Matplotlib, in deps)
```

Interactive click-to-inspect-trade-record is **out of scope** for v1 (Plotly callback support without Dash is non-trivial; deferred to future enhancement).

---

## 7. `TiConfig`

```python
@dataclass
class TiConfig:
    fee_per_share: float = 0.0035
    risk_free_rate: float = 0.04
    loan_rate: float = 0.0514            # borrowing cost for leveraged long positions
    stock_borrow_rate: float = 0.07      # short-selling borrow fee
    initial_capital: float = 10_000
    bars_per_year: int = 252
```

---

## 8. Docs Updates Required (alongside implementation)

These doc updates must happen **before or alongside** their corresponding implementation steps, not deferred to Step 11:

| File | Change |
|---|---|
| `api/index.md` | `fetch_data` signature `-> pd.DataFrame` → `-> dict[str, pd.DataFrame]` |
| `api/index.md` | `context.prices` description: remove "sliced to current evaluation date"; clarify it is the full history dict |
| `api/index.md` | `Backtest` `data` parameter type: `pd.DataFrame` → `dict[str, pd.DataFrame]` |
| `api/index.md` | Add `Select.Filter` to the Select table |
| `api/index.md` | Add `Trades.sample(n)` description under Trade Records |
| `api/index.md` | Add `validate_data` to the public API |
| `market-volatility-rebalance.md` | Replace `context.selected_child` references with the actual mechanism: `Signal.VIX` writes to `context.selected` and `context.weights` |
| `extra-data.md` | Add `ti.validate_data()` usage example |
| `allocation-strategies.md` | Add `import pandas as pd` to the Volatility Targeting snippet |

---

## 9. Testing Approach

- **No network calls in tests.** All tests use local CSV fixtures in `tests/data/` (three tickers: `QQQ`, `BIL`, `GLD`; daily bars; at least 3 years of data).
- **Unit tests** for each algo: deterministic inputs → assert exact `context.selected`, `context.weights`, return value.
- **Integration tests**: run `ti.run(ti.Backtest(...))` end-to-end against fixtures; assert `result.summary()` values are within tolerance.
- **Short-selling test**: dollar-neutral fixture; verify negative positions accumulate borrow costs correctly.
- **Tree structure test**: VIX regime-switching; assert correct child activation and full position liquidation on regime change.
- **Carry cost test**: assert daily borrow cost reduces `portfolio.cash` on the correct bars.
- **`validate_data` test**: assert `ValueError` is raised on misaligned indices with the correct date in the message.

---

## 10. Implementation Order

Build in this sequence to respect dependencies:

1. `config.py` — `TiConfig` dataclass
2. `algo.py` — `Context`, `Algo`, `AlgoQueue`, `Or`, `And`, `Not`
3. `portfolio.py` — `Portfolio` (state only, no engine logic)
4. `algos/signal.py` — `Signal.Schedule`, `Signal.Monthly`, `Signal.Quarterly`, `Signal.VIX`
5. `algos/select.py` — `Select.All`, `Select.Momentum`, `Select.Filter`
6. `algos/weigh.py` — `Weigh.Equally`, `Weigh.Ratio` first; then `Weigh.BasedOnHV`, `Weigh.ERC`, `Weigh.BasedOnBeta`
7. `algos/rebalance.py` — `Action.Rebalance`, `Action.PrintInfo`
8. `backtest.py` — simulation loop, trade execution, carry costs, mark-to-market, `BacktestResult`, `_SingleResult`, `Trades`
9. Metrics and charting — `summary()`, `full_summary()`, `plot()` family (Matplotlib first, Plotly second)
10. `__init__.py` — wire up public API, add `validate_data`, `fetch_data` wrapper
11. Docs fixes listed in Section 8 — update `api/index.md`, guides
