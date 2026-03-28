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

`algo.py` stays small and stable (just the ABC + AlgoQueue + branching). `algos/` holds growing concrete implementations grouped by category. Re-exports in `algos/__init__.py` keep the public namespace identical: `ti.Signal.Monthly` works regardless of internal file layout.

---

## Package Structure

```
src/tiportfolio/
  __init__.py         # Public API: fetch_data, Portfolio, Backtest, BacktestResult, run, Signal, Select, Weigh, Action, Or, And, Not
  config.py           # TiConfig dataclass with defaults
  algo.py             # Algo ABC + AlgoQueue + Or/And/Not
  branching.py        # Thin re-export shim: "from tiportfolio.algo import Or, And, Not"
                      # Re-exports into __init__.py so ti.Or / ti.And / ti.Not work at the top level
  algos/
    __init__.py       # Re-exports all concrete algos → accessible as ti.algo.*
    signal.py         # Signal namespace (Signal.Schedule, Signal.Monthly, Signal.Quarterly) + VixSignal
    select.py         # Select namespace (Select.All, Select.Momentum)
    weigh.py          # Weigh namespace: Weigh.Equally, Weigh.Ratio, Weigh.BasedOnHV, Weigh.BasedOnBeta, Weigh.ERC
    rebalance.py      # Action namespace: Action.Rebalance, Action.PrintInfo
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
    # child portfolio chosen by a signal algo (e.g. VixSignal); read by the engine
```

The three mutable fields (`selected`, `weights`, `selected_child`) form the inter-algo communication contract:
- **Select algos** write `context.selected`
- **Weigh algos** read `context.selected`, write `context.weights`
- **Action.Rebalance** reads `context.weights` to execute trades
- **Signal algos** write `context.selected_child`
- **Engine** reads `context.selected_child` to fork and evaluate the selected child

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

### `AlgoQueue` (in `algo.py`)

```python
class AlgoQueue(Algo):
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
    """All algos must return True. Explicit version of AlgoQueue for use inside Or/Not."""
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
        children: list[str] | list[Portfolio] | list[str | Portfolio] | None = None,
    ): ...
```

- `children` is optional (defaults to `None`)
- Accepts `list[str]` (tickers), `list[Portfolio]` (sub-portfolios), mixed, or `None`
- `algos` is internally wrapped in `AlgoQueue`

---

## Backtest + Result

### `TiConfig` (in `config.py`)

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
        ti.Signal.Monthly(),
        ti.Select.All(),
        ti.Weigh.Equally(),
        ti.Action.Rebalance(),
    ],
    ["QQQ", "BIL", "GLD"],
)

# 3. Run
result = ti.run(ti.Backtest(portfolio, data))

# 4. Inspect
result.summary()
result.plot()
result.trades
```

Namespaces exposed directly under `ti`:
- `ti.run` — entry point
- `ti.Signal`, `ti.Select`, `ti.Weigh`, `ti.Action` — algo namespaces (Signal includes both time-based and market-based algos)
- `ti.Or`, `ti.And`, `ti.Not`

---

## Concrete Algo Catalogue

### Signal algos (`algos/signal.py`)

Signal algos are the first step in any `AlgoQueue` — they control *when* to proceed and *which branch* receives capital. Two sub-types live in the same file:

**Time-based signals** — `Signal` is a namespace; `Signal.Schedule` is the primitive; `Signal.Monthly` and `Signal.Quarterly` are proxy subclasses:

| Class | Description |
|---|---|
| `Signal.Schedule(month=None, day="end", next_trading_day=True)` | Base — fires on `day` of `month`; every month if `month=None` |
| `Signal.Monthly(day="end", next_trading_day=True)` | Proxy → `Signal.Schedule`: monthly preset |
| `Signal.Quarterly(months=[2,5,8,11], day="end")` | Proxy → `Or(Signal.Schedule(month=m) for m in months)`: quarterly preset |

**Market-based signals** — fire based on market data; route capital to child portfolios:

| Class | Description |
|---|---|
| `Signal.VIX(high: float, low: float, data: pd.DataFrame)` | Sets `context.selected_child` based on VIX regime; reads `close` from `data` DataFrame |

`Signal.VIX` takes a pre-fetched OHLCV DataFrame (via `ti.fetch_data`). When VIX > `high`, second child selected; when VIX < `low`, first child selected; between thresholds, previous selection persists.

### Select algos (`algos/select.py`)

`Select` is a namespace. `Select.All` is the standard selector; `Select.Momentum` is a direct implementation that computes momentum scores:

| Class | Description |
|---|---|
| `Select.All()` | Selects all tickers in the portfolio |
| `Select.Momentum(n, lookback, lag, sort_descending=True)` | Selects top/bottom `n` tickers by momentum score; writes to `context.selected` |

### Weigh algos (`algos/weigh.py`)

`Weigh` is a namespace. `Weigh.Ratio` accepts an explicit weights dict; all other variants compute their specific scheme and write to `context.weights`:

| Class | Description |
|---|---|
| `Weigh.Equally(short: bool = False)` | Equal weight; `short=True` for short leg |
| `Weigh.Ratio(weights: dict[str, float])` | Applies provided weights (normalised to sum to 1) |
| `Weigh.BasedOnHV(initial_ratio, target_hv, lookback)` | Volatility targeting |
| `Weigh.BasedOnBeta(initial_ratio, target_beta, lookback, base_data)` | Beta neutral; `base_data` is the benchmark OHLCV DataFrame |
| `Weigh.ERC(lookback, covar_method="ledoit-wolf", risk_parity_method="ccd", maximum_iterations=100, tolerance=1e-8)` | Equal Risk Contribution (Risk Parity) |

### Action algos (`algos/rebalance.py`)

| Class | Description |
|---|---|
| `Action.Rebalance()` | Executes trades to reach target weights |
| `Action.PrintInfo()` | Debug: logs current context state |

### Tree Portfolio Execution Protocol

For a parent portfolio with children, the simulation evaluates depth-first:

1. Parent's `AlgoQueue` runs on the current `Context`
2. A signal algo (e.g. `Signal.VIX`) sets `context.selected_child` to one of `portfolio.children`
3. If the parent stack returns `True`, the engine automatically routes capital to `selected_child` and evaluates it with a **forked `Context`** (same `prices`/`date`/`config`, fresh `selected`/`weights`/`selected_child`, `portfolio` = child)
5. The child's `AlgoQueue` runs normally (schedule → select → weigh → rebalance)
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
