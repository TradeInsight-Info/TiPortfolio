# Package Structure

```
src/tiportfolio/
├── __init__.py             # Public API exports
├── config.py               # TiConfig — global backtest defaults
├── algo.py                 # Algo ABC, AlgoQueue, Context, Or, And, Not
├── algos/                  # Concrete algo implementations
│   ├── __init__.py         # Re-exports all algos → accessible as ti.Signal.*, ti.Select.*, ti.Weigh.*, ti.Action.*
│   ├── signal.py           # All signal algos: time-based (Schedule*) + market-based (VixSignal)
│   ├── select.py           # Universe selection algos
│   ├── weigh.py            # Weight calculation algos
│   └── rebalance.py        # Trade execution + debug algos
├── portfolio.py            # Portfolio tree node
├── backtest.py             # Backtest, run(), _apply_leverage(), simulation engine
└── helpers/                # Data layer (YFinance, Alpaca, cache, logging)
    ├── __init__.py
    ├── cache.py            # Disk cache for data fetches
    ├── common.py           # DataCol enum, BarData, FeeMode shared types
    ├── data.py             # DataSource ABC, YFinance, Alpaca implementations
    ├── log.py              # Logger with progress bar support
    └── scope.py            # StaticScope singleton (internal registry)
```

---

## File Responsibilities

### `__init__.py` — Public API

Exports the symbols users import directly:

```python
from tiportfolio import (
    fetch_data,
    Portfolio,
    Backtest,
    BacktestResult,
    TiConfig,
    run,         # accepts *tests for multi-backtest comparison
    Signal,      # ti.Signal.Monthly(), ti.Signal.Quarterly(), ti.Signal.Schedule(), ti.Signal.VIX()
    Select,      # ti.Select.All(), ti.Select.Momentum()
    Weigh,       # ti.Weigh.Equally(), ti.Weigh.Ratio(), ti.Weigh.BasedOnHV(), ti.Weigh.BasedOnBeta(), ti.Weigh.ERC()
    Action,      # ti.Action.Rebalance(), ti.Action.PrintInfo()
    Or,          # ti.Or(...)
    And,         # ti.And(...)
    Not,         # ti.Not(...)
)
```

Nothing else is part of the public contract. Internal modules may change without notice.

---

### `config.py` — `TiConfig`

A `dataclass` holding global defaults passed to every `Backtest`. Values can be overridden per-backtest. Kept in its own file so it can be imported by `algo.py`, `portfolio.py`, and `backtest.py` without circular imports.

```python
@dataclass
class TiConfig:
    fee_per_share: float = 0.0035
    risk_free_rate: float = 0.04
    loan_rate: float = 0.0514         # borrowing cost for leveraged positions
    stock_borrow_rate: float = 0.07   # short-selling borrow fee; varies by security
    initial_capital: float = 10_000
    bars_per_year: int = 252
```

---

### `algo.py` — Core Abstractions

Contains the stable interface layer. Should not import from `algos/`.

| Symbol | Role |
|---|---|
| `Context` | Dataclass passed to every algo — holds `portfolio`, `prices`, `date`, `config` (read-only) and `selected`, `weights` (mutable), `_execute_leaf`, `_allocate_children` (callbacks) |
| `Algo` | Abstract base class; one method: `__call__(context) -> bool` |
| `AlgoQueue` | Runs algos sequentially; stops on first `False` (logical AND) |
| `Or` | `Or(*algos)` — runs branches until one returns `True` (logical OR) |
| `And` | `And(*algos)` — all must return `True`; explicit version of `AlgoQueue` |
| `Not` | `Not(algo)` — inverts result of wrapped algo |

**Inter-algo communication contract via `Context`:**

| Field | Written by | Read by |
|---|---|---|
| `selected: list[str]` | Select algos | Weigh algos, Rebalance |
| `weights: dict[str, float]` | Weigh algos | Rebalance |

---

### `algos/` — Concrete Implementations

All concrete algos. Internal files are organized by the *role* each algo plays in the stack:

| File | Role in stack | Algos |
|---|---|---|
| `signal.py` | **When / which branch** — time-based and market-based signals | `Signal` namespace: `Signal.Schedule` (base), `Signal.Monthly`, `Signal.Quarterly`, `Signal.Weekly`, `Signal.Yearly`, `Signal.Once`, `Signal.EveryNPeriods`, `Signal.VIX`, `Signal.Indicator` |
| `select.py` | **What** to include | `Select` namespace: `Select.All`, `Select.Momentum` |
| `weigh.py` | **How much** to allocate | `Weigh` namespace: `Weigh.Equally`, `Weigh.Ratio`, `Weigh.BasedOnHV`, `Weigh.BasedOnBeta`, `Weigh.ERC` |
| `rebalance.py` | **Action** — execute trades | `Action` namespace: `Action.Rebalance`, `Action.PrintInfo` |

`algos/__init__.py` re-exports everything so `ti.Signal.Monthly` resolves correctly.

---

### `portfolio.py` — `Portfolio`

A tree node that owns an `AlgoQueue` and optionally child `Portfolio` nodes. Represents a single strategy or a sub-strategy within a multi-regime parent.

```python
class Portfolio:
    name: str
    algos: AlgoQueue                                              # built from the list passed to __init__
    children: list[str] | list[Portfolio] | list[str | Portfolio] | None  # optional, default None
```

`children` accepts:
- `None` (default) — no fixed universe
- `list[str]` — leaf node; tradeable ticker symbols
- `list[Portfolio]` — parent node; sub-strategies
- `list[str | Portfolio]` — mixed tickers and child portfolios

The engine detects node type at runtime. A parent uses signal algos to select one child on each date; a leaf runs its stack directly against its ticker symbols.

---

### `backtest.py` — Simulation Engine

| Symbol | Role |
|---|---|
| `Backtest` | Bundles `Portfolio` + `data` + `TiConfig` |
| `BacktestResult` | Holds equity curves; provides `summary()`, `full_summary()`, `plot()`, `plot_histogram()`, `plot_security_weights()`. Access individual results via `result[0]` or `result["name"]`. Trade records are on individual results: `result[0].trades`. |
| `run(*tests, leverage=1.0)` | Entry point; accepts multiple backtests for comparison |

The simulation loop:
1. For each trading day in `data`
2. Evaluate the `Portfolio` tree (root first, depth-first)
3. Each node runs its `AlgoQueue` with a `Context` scoped to that node's `tickers`
4. For a **leaf** node: if the stack returns `True`, execute trades toward `context.weights`; record the event in `trades`
5. For a **parent** node: a signal algo sets `context.selected`; if the stack returns `True`, the engine automatically forks a new `Context` for the selected child and evaluates it recursively
6. If any node's stack returns `False`, the entire subtree is skipped

---

### `helpers/` — Data Layer

Borrowed from [pybroker](https://github.com/edtechre/pybroker) (Apache 2.0). Do not modify without checking the upstream license.

| File | Responsibility |
|---|---|
| `data.py` | `DataSource` ABC; `YFinance` and `Alpaca`/`AlpacaCrypto` implementations. All sources normalize timestamps to UTC. |
| `cache.py` | Disk-based caching for data fetches (`diskcache`). Call `enable_data_source_cache()` to activate. |
| `common.py` | Shared types: `DataCol` enum, `BarData`, `FeeMode`, `FeeInfo` |
| `log.py` | `Logger` with tqdm-based progress bar |
| `scope.py` | `StaticScope` singleton — internal registry for columns, indicators, models. Used by the engine, not by user code. |

---

## Dependency Graph

```
__init__.py
    ├── backtest.py
    │     ├── portfolio.py
    │     │     └── algo.py
    │     │           └── config.py
    │     └── config.py
    ├── algos/  (all import from algo.py)
    └── helpers/  (standalone, no internal imports)
```

`config.py` and `helpers/` are the only modules with no intra-package dependencies — safe to import anywhere.

---

## Adding a New Algo

1. Pick the appropriate file in `algos/` (or create a new one for a new category)
2. Subclass `Algo` from `tiportfolio.algo`
3. Implement `__call__(self, context: Context) -> bool`
4. Add the export to `algos/__init__.py`

Example:

```python
# algos/signal.py  — add inside the Signal namespace class
from tiportfolio.algo import Algo, Context

class Signal:
    ...
    class Weekly(Algo):
        """Proxy → Signal.Schedule: triggers every Friday (or nearest trading day)."""
        def __call__(self, context: Context) -> bool:
            return context.date.dayofweek == 4  # Friday
```

```python
# algos/__init__.py  — re-export the updated Signal namespace
from tiportfolio.algos.signal import Signal
```
