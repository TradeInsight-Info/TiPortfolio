## Context

`result.py` has a working `_SingleResult` (summary with 4 metrics, matplotlib plot) and `BacktestResult` (collection, multi-comparison). The engine (`backtest.py`) runs trades via `execute_leaf_trades` but doesn't capture trade records. Plotly is in dev dependencies but not used.

## Goals / Non-Goals

**Goals:**
- Record every trade during execution without breaking existing engine performance
- `Trades` wrapper with full DataFrame delegation
- Extended metrics (Sortino, Calmar, max DD duration, monthly stats)
- New charts: security weights, histogram, interactive Plotly

**Non-Goals:**
- No changes to the engine loop or algo evaluation order
- No transaction cost modeling changes (fees already work)
- No PDF/HTML report generation (future work)
- No real-time charting or streaming updates

## Decisions

### 1. Trade recording via return value from execute_leaf_trades

**Choice**: `execute_leaf_trades` returns `list[dict]` of trade records. `_run_single` accumulates them across all dates.

**Alternative considered**: Store trades on the Portfolio object — rejected because Portfolio is a domain model, not a results container.

Each trade record dict:
```python
{
    "date": pd.Timestamp,
    "portfolio": str,           # portfolio.name
    "ticker": str,
    "qty_before": float,
    "qty_after": float,
    "delta": float,             # qty_after - qty_before
    "price": float,
    "fee": float,
    "equity_before": float,     # portfolio.equity before this rebalance
    "equity_after": float,      # portfolio.equity after all trades settle
}
```

`equity_after` is set post-rebalance by `_run_single` after mark-to-market on the next bar, or computed immediately from cash + positions.

### 2. Trades class with __getattr__ delegation

**Choice**: `Trades` stores a `pd.DataFrame` as `self._df` and delegates all attribute access via `__getattr__`. `__getitem__` also delegates for column access.

This is the standard "wrap and extend" pattern. `sample(n)` is the only custom method.

### 3. sample(n) deduplication

**Choice**: Concat `nlargest(n)` and `nsmallest(n)` on `equity_return` column (computed as `equity_after - equity_before`), then deduplicate with `~df.index.duplicated()`.

### 4. Sortino ratio implementation

Sortino = `(mean_excess * sqrt(bars_per_year)) / downside_std` where downside_std only uses negative excess returns. If no negative returns, return 0.0.

### 5. Max drawdown duration

Count bars from each drawdown peak to recovery (or end of series). Return the maximum count.

### 6. Plotly lazy import

**Choice**: `import plotly` inside `plot()` only when `interactive=True`. This keeps plotly optional — no import-time error if not installed. Raise `ImportError` with helpful message if missing.

### 7. Weight recording for plot_security_weights

**Choice**: Record weights at each rebalance date alongside trades. Add a `weight_history: list[dict]` to `_SingleResult` with entries `{date, ticker, weight}`. `execute_leaf_trades` already has `context.weights` — capture it.

## Risks / Trade-offs

- **[Performance of trade recording]** → Each trade creates a dict. For 252 days * 5 assets * 5 years = ~6300 records — negligible memory. Mitigation: none needed.
- **[Plotly as optional dependency]** → Users without plotly get `ImportError` at runtime. Mitigation: clear error message with install instructions.
- **[equity_after timing]** → Recording equity_after accurately requires a mark-to-market after trades settle. Mitigation: compute it inline as `cash + sum(qty * price)` immediately after trade execution.
