# Package Structure

```
src/tiportfolio/
├── __init__.py             # Public API exports
├── config.py               # TiConfig — global backtest defaults
├── algo.py                 # Algo ABC, AlgoStack, Context, Or, Not
├── branching.py            # Re-export shim: exposes Or/Not as ti.branching.*
├── algos/                  # Concrete algo implementations
│   ├── __init__.py         # Re-exports all algos → accessible as ti.algo.*
│   ├── schedule.py         # Time-based trigger algos
│   ├── select.py           # Universe selection algos
│   ├── weigh.py            # Weight calculation algos
│   ├── rebalance.py        # Trade execution + debug algos
│   └── signal.py           # Regime signal algos
├── portfolio.py            # Portfolio tree node
├── backtest.py             # Backtest, BacktestResult, run_backtest()
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
    run,         # replaces run_backtest; accepts *tests for multi-backtest comparison
    algo,        # module: ti.algo.*
    branching,   # module: ti.branching.*
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
    initial_capital: float = 10_000
    bars_per_year: int = 252
    benchmark: str = "SPY"
```

---

### `algo.py` — Core Abstractions

Contains the stable interface layer. Should not import from `algos/`.

| Symbol | Role |
|---|---|
| `Context` | Dataclass passed to every algo — holds `portfolio`, `prices`, `date`, `config` (read-only) and `selected`, `weights`, `selected_child` (mutable, inter-algo communication) |
| `Algo` | Abstract base class; one method: `__call__(context) -> bool` |
| `AlgoStack` | Runs algos sequentially; stops on first `False` (logical AND) |
| `Or` | `Or(*algos)` — runs branches until one returns `True` (logical OR) |
| `And` | `And(*algos)` — all must return `True`; explicit version of `AlgoStack` |
| `Not` | `Not(algo)` — inverts result of wrapped algo |

**Inter-algo communication contract via `Context`:**

| Field | Written by | Read by |
|---|---|---|
| `selected: list[str]` | Select algos | Weigh algos, Rebalance |
| `weights: dict[str, float]` | Weigh algos, WeighSelected | Rebalance |
| `selected_child: Portfolio \| None` | Signal algos (VixSignal) | WeighSelected, engine |

---

### `algos/` — Concrete Implementations

All concrete algos. Internal files are organized by the *role* each algo plays in the stack:

| File | Role in stack | Algos |
|---|---|---|
| `schedule.py` | **When** to rebalance | `ScheduleMonthly`, `ScheduleQuarterly`, `Schedule` |
| `select.py` | **What** to include | `SelectAll`, `SelectMomentum` |
| `weigh.py` | **How much** to allocate | `WeighEqually`, `WeighFixedRatio`, `WeighBasedOnHV`, `WeighBasedOnBeta` |
| `rebalance.py` | **Action** — execute trades | `Rebalance`, `PrintInfo` |
| `signal.py` | **Route** between child portfolios | `VixSignal`, `WeighSelected` |

`algos/__init__.py` re-exports everything so `ti.algo.ScheduleMonthly` resolves correctly.

---

### `portfolio.py` — `Portfolio`

A tree node that owns an `AlgoStack` and optionally child `Portfolio` nodes. Represents a single strategy or a sub-strategy within a multi-regime parent.

```python
class Portfolio:
    name: str
    algos: AlgoStack                      # built from the list passed to __init__
    children: list[str | Portfolio]       # ticker strings (leaf) or sub-portfolios (parent)
```

`children` unifies the two cases in the tree:
- **Leaf node**: `children = ["QQQ", "BIL", "GLD"]` — tradeable symbols
- **Parent node**: `children = [low_vol_portfolio, high_vol_portfolio]` — sub-strategies

The engine detects whether a node is a leaf (all children are `str`) or a parent (children contain `Portfolio`). A parent uses signal algos to select one child portfolio on each date; a leaf runs its stack directly against its ticker symbols.

---

### `backtest.py` — Simulation Engine

| Symbol | Role |
|---|---|
| `Backtest` | Bundles `Portfolio` + `data` + `TiConfig` |
| `BacktestResult` | Holds `trades: pd.DataFrame`; provides `summary()`, `plot()`, `plot_histogram()`, `plot_security_weights()` |
| `run_backtest(test)` | Entry point — iterates trading days, evaluates portfolio tree, records trades |

The simulation loop:
1. For each trading day in `data`
2. Evaluate the `Portfolio` tree (root first, depth-first)
3. Each node runs its `AlgoStack` with a `Context` scoped to that node's `tickers`
4. For a **leaf** node: if the stack returns `True`, execute trades toward `context.weights`; record the event in `trades`
5. For a **parent** node: a signal algo sets `context.selected_child`; `WeighSelected` records the weight; if the stack returns `True`, the engine forks a new `Context` for the selected child and evaluates it recursively
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
# algos/schedule.py
from tiportfolio.algo import Algo, Context

class ScheduleWeekly(Algo):
    """Triggers every Friday (or nearest trading day)."""
    def __call__(self, context: Context) -> bool:
        return context.date.dayofweek == 4  # Friday
```

```python
# algos/__init__.py  — add to existing exports
from tiportfolio.algos.schedule import ScheduleMonthly, ScheduleQuarterly, Schedule, ScheduleWeekly
```
