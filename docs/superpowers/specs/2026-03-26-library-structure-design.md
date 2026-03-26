# TiPortfolio Library Structure Design

**Date:** 2026-03-26
**Status:** Approved
**Branch:** simplify

---

## Problem

The existing implementation was deleted to start fresh. The goal is to redesign TiPortfolio as an algo-stack–based portfolio backtesting library (inspired by `bt`), replacing the old flat `ScheduleBasedEngine` API with a composable, extensible design.

---

## Design Goals

- **Library-first**, with CLI support
- **Algo-stack composability**: strategies are built by stacking `Algo` objects in a `Portfolio`
- **Tree structure**: portfolios can be nested (parent/child) for regime-switching and multi-strategy scenarios
- **Extensible**: users can implement custom `Algo` subclasses
- **Cost-aware**: transaction fees baked into every backtest
- **Simple public API**: `ti.fetch_data()` → `ti.Portfolio()` → `ti.run_backtest()` → `result.summary()`

---

## Chosen Approach: Flat Core + `algos/` Subpackage

Selected over:
- Pure flat files (algo.py grows unbounded as implementations expand)
- Deep `core/` nesting (premature for current scope)

### Rationale

`algo.py` stays small and stable (just the ABC + AlgoStack + branching). `algos/` holds growing concrete implementations grouped by category. Re-exports in `algos/__init__.py` keep the public namespace identical: `ti.algo.ScheduleMonthly` works regardless of internal file layout.

---

## Package Structure

```
src/tiportfolio/
  __init__.py         # Public API: fetch_data, Portfolio, Backtest, BacktestResult, run_backtest, algo, branching
  config.py           # TiConfig dataclass with defaults
  algo.py             # Algo ABC + AlgoStack + Or/Not (Or and Not also re-exported via branching.py)
  branching.py        # Thin re-export shim: "from tiportfolio.algo import Or, And, Not"
                      # Makes ti.branching.Or / ti.branching.And / ti.branching.Not work as a distinct namespace
  algos/
    __init__.py       # Re-exports all concrete algos → accessible as ti.algo.*
    schedule.py       # ScheduleMonthly, ScheduleQuarterly, Schedule
    select.py         # SelectAll, SelectMomentum
    weigh.py          # WeighEqually, WeighFixedRatio, WeighBasedOnHV, WeighBasedOnBeta
    rebalance.py      # Rebalance, PrintInfo
    signal.py         # VixSignal, WeighSelected
  portfolio.py        # Portfolio tree node
  backtest.py         # Backtest, BacktestResult, run_backtest()
  helpers/            # Data layer (existing — Alpaca, YFinance, cache, log)
    __init__.py
    cache.py
    common.py
    data.py
    log.py
    scope.py
```

---

## Core Abstractions

### `Context` (in `algo.py`)

Passed to every `Algo.__call__`. Holds all state an algo needs to make decisions.

```python
@dataclass
class Context:
    portfolio: Portfolio
    prices: pd.DataFrame           # full price history up to current date
    date: pd.Timestamp             # current rebalance evaluation date
    config: TiConfig
    selected: list[str] = field(default_factory=list)
    # tickers selected by a Select algo; read by Weigh and Rebalance algos
    weights: dict[str, float] = field(default_factory=dict)
    # target weights written by a Weigh algo; read by Rebalance
    selected_child: Portfolio | None = None
    # child portfolio chosen by a signal algo (e.g. VixSignal); read by WeighSelected
```

The three mutable fields (`selected`, `weights`, `selected_child`) form the inter-algo communication contract:
- **Select algos** write `context.selected`
- **Weigh algos** read `context.selected`, write `context.weights`
- **Rebalance** reads `context.weights` to execute trades
- **Signal algos** write `context.selected_child`
- **WeighSelected** reads `context.selected_child` to assign parent weight

### `Algo` ABC (in `algo.py`)

```python
class Algo(ABC):
    @abstractmethod
    def __call__(self, context: Context) -> bool:
        """
        Execute the algo step.
        Returns True to continue the stack, False to stop (skip rebalance).
        """
```

All concrete algos — schedulers, selectors, weighers, actions, signals — implement this single interface.

### `AlgoStack` (in `algo.py`)

```python
class AlgoStack(Algo):
    """
    Sequential pipeline of Algos.
    Runs each Algo in order; stops and returns False if any returns False.
    Equivalent to logical AND across all steps.
    """
    def __init__(self, *algos: Algo): ...
    def __call__(self, context: Context) -> bool: ...
```

### Branching (in `algo.py`)

```python
class Or(Algo):
    """Runs each algo in order; returns True on first that returns True."""
    def __init__(self, *algos: Algo): ...

class And(Algo):
    """All algos must return True. Explicit version of AlgoStack for use inside Or/Not."""
    def __init__(self, *algos: Algo): ...

class Not(Algo):
    """Inverts the result of a wrapped Algo."""
    def __init__(self, algo: Algo): ...
```

---

## Portfolio

```python
class Portfolio:
    def __init__(
        self,
        name: str,
        algos: list[Algo],
        children: list[str | Portfolio],
    ): ...
```

- `children`: accepts ticker strings (leaf node) or nested `Portfolio` objects (parent node)
- `algos` is internally wrapped in `AlgoStack`
- The engine distinguishes leaf vs parent by inspecting whether `children` contains strings or `Portfolio` objects

---

## Backtest + Result

### `TiConfig` (in `config.py`)

```python
@dataclass
class TiConfig:
    fee_per_share: float = 0.0035
    risk_free_rate: float = 0.04
    initial_capital: float = 10_000
    bars_per_year: int = 252
    benchmark: str | None = None   # optional; when set, runs a buy-and-hold on that ticker for comparison
```

### `Backtest` (in `backtest.py`)

```python
class Backtest:
    def __init__(
        self,
        portfolio: Portfolio,
        data: pd.DataFrame,
        fee_per_share: float | None = None,   # override TiConfig
        config: TiConfig | None = None,
    ): ...
```

### `BacktestResult` (in `backtest.py`)

```python
@dataclass
class BacktestResult:
    trades: pd.DataFrame    # one row per rebalance; columns: date, equity_before,
                            # equity_after, fee_paid, {TICKER}_price,
                            # {TICKER}_qty_before, {TICKER}_trade_qty,
                            # {TICKER}_qty_after, {TICKER}_value_after

    def summary(self) -> dict[str, float]:
        """Quick overview. Returns: start, end, risk_free_rate, total_return, cagr,
           daily_sharpe, daily_sortino, max_drawdown, calmar, kelly,
           final_value, total_fee, rebalance_count"""

    def full_summary(self) -> dict[str, float]:
        """Complete performance report. Includes all summary() fields plus:
           Period returns: mtd, 3m, 6m, ytd, 1y, 3y_ann, 5y_ann, 10y_ann, incep_ann
           Daily stats:    daily_mean_ann, daily_vol_ann, daily_skew, daily_kurt,
                           best_day, worst_day
           Monthly stats:  monthly_sharpe, monthly_sortino, monthly_mean_ann,
                           monthly_vol_ann, monthly_skew, monthly_kurt,
                           best_month, worst_month
           Yearly stats:   yearly_sharpe, yearly_sortino, yearly_mean, yearly_vol,
                           yearly_skew, yearly_kurt, best_year, worst_year
           Drawdown:       avg_drawdown, avg_drawdown_days, avg_up_month,
                           avg_down_month, win_year_pct, win_12m_pct"""

    def plot(self) -> None:
        """Equity curve with interactive hover (performance) and click (trade records)."""

    def plot_histogram(self) -> None:
    def plot_security_weights(self) -> None:
```

### `run` (in `backtest.py`)

```python
def run(*tests: Backtest) -> BacktestResult: ...
```

Accepts one or more `Backtest` objects. The returned `BacktestResult` is always collection-aware:
- **Single test**: `summary()` returns `dict[str, float]`; charts show one portfolio
- **Multiple tests**: `summary()` returns `pd.DataFrame` (metrics × portfolios); charts overlay all portfolios for comparison
- Individual results accessible via `result["name"]` or `result[index]`

---

## Public API (`__init__.py`)

```python
import tiportfolio as ti

# 1. Fetch data
data = ti.fetch_data(["QQQ", "BIL", "GLD"], start="2019-01-01", end="2024-12-31")

# 2. Build strategy
portfolio = ti.Portfolio(
    "monthly_rebalance",
    [
        ti.algo.ScheduleMonthly(),
        ti.algo.SelectAll(),
        ti.algo.WeighEqually(),
        ti.algo.Rebalance(),
    ],
    children=["QQQ", "BIL", "GLD"],
)

# 3. Run
result = ti.run(ti.Backtest(portfolio, data))

# 4. Inspect
result.summary()
result.plot()
result.trades
```

Namespaces exposed:
- `ti.run` — entry point (replaces `run_backtest`)
- `ti.algo.*` — all concrete algos (via `algos/__init__.py` re-exports)
- `ti.branching.Or`, `ti.branching.And`, `ti.branching.Not`

---

## Concrete Algo Catalogue

### Schedule algos (`algos/schedule.py`)

`Schedule` is the primitive. `ScheduleMonthly` and `ScheduleQuarterly` are thin convenience wrappers that construct the appropriate `Schedule` (or `Or`-wrapped `Schedule`) internally.

| Class | Description |
|---|---|
| `Schedule(month=None, day="end", next_trading_day=True)` | Primitive trigger — fires on `day` of `month`; if `month=None`, fires every month |
| `ScheduleMonthly(day="end", next_trading_day=True)` | Convenience wrapper: `Schedule(day=day, next_trading_day=next_trading_day)` |
| `ScheduleQuarterly(months=[2,5,8,11], day="end")` | Convenience wrapper: `Or(Schedule(month=m, day=day) for m in months)` |

### Select algos (`algos/select.py`)

| Class | Description |
|---|---|
| `SelectAll()` | Selects entire universe |
| `SelectMomentum(n, lookback, lag, sort_descending=True)` | Selects top/bottom n by momentum |

### Weigh algos (`algos/weigh.py`)

| Class | Description |
|---|---|
| `WeighEqually(sign=1)` | Equal weight; sign=-1 for short leg |
| `WeighFixedRatio(weights: dict[str, float])` | Fixed target weights |
| `WeighBasedOnHV(initial_ratio, target_hv, lookback)` | Volatility targeting |
| `WeighBasedOnBeta(initial_ratio, target_beta, lookback)` | Beta neutral |
| `WeighERC(lookback, covar_method="ledoit-wolf", risk_parity_method="ccd", maximum_iterations=100, tolerance=1e-8)` | Equal Risk Contribution (Risk Parity) |

### Action algos (`algos/rebalance.py`)

| Class | Description |
|---|---|
| `Rebalance()` | Executes trades to reach target weights |
| `PrintInfo()` | Debug: logs current context state |

### Signal algos (`algos/signal.py`)

| Class | Description |
|---|---|
| `VixSignal(high: float, low: float, signal: pd.DataFrame)` | Selects child portfolio based on VIX regime; `signal` is a pre-fetched OHLCV DataFrame for VIX |
| `WeighSelected(weight: float)` | Assigns weight to the selected child |

`VixSignal` takes `signal: pd.DataFrame` (a pre-fetched OHLCV DataFrame for VIX, fetched separately via `ti.fetch_data`). This keeps algos stateless and testable — they never fetch data internally. The algo reads the `close` column from the DataFrame to compare against `high`/`low` thresholds. When VIX > `high`, the second child is selected (high-volatility portfolio); when VIX < `low`, the first child is selected (low-volatility); between the thresholds, the previous selection persists.

`WeighSelected` reads `context.selected_child` and writes a `{child.name: weight}` entry to `context.weights`, which the parent's `Rebalance` algo then uses to allocate capital to the child.

### Tree Portfolio Execution Protocol

For a parent portfolio with children, the simulation evaluates depth-first:

1. Parent's `AlgoStack` runs on the current `Context`
2. A signal algo (e.g. `VixSignal`) sets `context.selected_child` to one of `portfolio.children`
3. `WeighSelected` writes the child's weight to `context.weights`
4. If the parent stack returns `True`, the engine evaluates the selected child with a **forked `Context`** (same `prices`/`date`/`config`, fresh `selected`/`weights`/`selected_child`, `portfolio` = child)
5. The child's `AlgoStack` runs normally (schedule → select → weigh → rebalance)
6. The child may itself have children, enabling arbitrarily deep nesting

If the parent stack returns `False`, no child is evaluated (rebalance skipped for this subtree).

---

## Extension Points

Custom algos: subclass `Algo`, implement `__call__(self, context: Context) -> bool`.

```python
class MyCustomTrigger(ti.Algo):
    def __call__(self, context: Context) -> bool:
        # return True to continue stack, False to skip rebalance
        ...
```

Custom data sources: subclass `helpers.data.DataSource`.

---

## Out of Scope (for this design)

- CLI (`ti` command) — Dimension 4, separate implementation
- AI skills integration — Dimension 5
- Risk management algos (Tail Risk, Drawdown Control) — Dimension 3
- PDF reports — future charting enhancement
