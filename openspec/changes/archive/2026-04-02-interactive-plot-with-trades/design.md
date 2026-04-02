## Context

Currently `_SingleResult.plot()` renders a matplotlib chart with a single total equity line and drawdown subplot. The engine already records `_trade_records` (with date, ticker, delta, price, qty_before, qty_after) and `_weight_history`, but does NOT store the price DataFrames or per-asset position snapshots over time. Per-asset equity must be reconstructed from trade records + prices.

## Goals / Non-Goals

**Goals:**
- Add `plot_interactive()` method returning a Plotly `Figure` with per-asset + total equity lines and trade markers
- Reconstruct per-asset equity from existing trade records + stored prices
- Trade markers: green up-triangles (buy) and red down-triangles (sell) with dotted vertical lines
- Hover tooltips on all elements
- PNG export via `fig.write_image()`

**Non-Goals:**
- Not changing the existing `plot()` matplotlib method
- Not adding per-asset tracking to the engine loop (reconstruct from existing data instead)
- Not adding drawdown subplot to the interactive chart (keep it focused on equity + trades)

## Decisions

### 1. Store prices on `_SingleResult`
**Decision**: Pass the `backtest.data` dict (ticker → DataFrame) into `_SingleResult.__init__` as a new `_prices` parameter.
**Rationale**: Per-asset equity = `qty × close_price` requires price data. The engine already has it in `Backtest.data`; we just need to thread it through to the result. Low memory cost since it's the same dict reference.
**Alternative**: Reconstruct prices from trade records alone — rejected because trade records only have prices on rebalance dates, not every bar.

### 2. Reconstruct per-asset equity via forward-fill
**Decision**: Build a `_per_asset_equity()` helper on `_SingleResult` that:
1. Creates a `positions_df` from `_trade_records`: for each (date, ticker), use `qty_after`
2. Forward-fills quantities across all dates in the equity curve index
3. Multiplies `qty × close_price` per ticker per date
**Rationale**: This gives daily per-asset values without modifying the engine loop. Trade records already have all the data needed.

### 3. Trade markers grouped by date
**Decision**: Group trades by date. On a given rebalance date, there may be multiple buys and sells. Show one marker per (date, ticker) pair, positioned on the total equity line's y-value for that date.
**Rationale**: Markers on the total equity line are visually cleaner than scattering them across individual asset lines.

### 4. Multi-backtest comparison mode
**Decision**: `BacktestResult.plot_interactive()` has two modes:
- **Single backtest** (1 result): delegates to `_SingleResult.plot_interactive()` — shows per-asset breakdown + trade markers
- **Multi-backtest** (2+ results): overlays total equity lines for each strategy with distinct colours, plus buy/sell markers per strategy (colour-matched, togglable via legend). No per-asset breakdown in multi mode (too noisy).
**Rationale**: Single-backtest deep dives need per-asset detail. Multi-backtest comparisons need clean overlaid totals. Trade markers in multi mode let users see when each strategy trades relative to others.
**Alternative**: Always show per-asset lines for all strategies — rejected because with 3 strategies × 3 assets = 9 lines + markers would be unreadable.

### 5. Plotly for interactivity, kaleido for PNG
**Decision**: Use `plotly.graph_objects` for the interactive chart. PNG export uses `fig.write_image()` which requires the `kaleido` package.
**Rationale**: Plotly is already an optional dependency. `kaleido` is the standard Plotly static export engine.

## Risks / Trade-offs

- **[Risk] Large number of trade markers clutters the chart** → Mitigation: use small marker size, semi-transparent vertical lines (opacity=0.3), and Plotly's legend toggle to hide/show trade markers
- **[Risk] kaleido not installed** → Mitigation: `write_image()` raises a clear ImportError from Plotly itself; document in docstring
- **[Trade-off] Markers on total equity line vs per-asset lines** → Chose total equity for visual clarity; per-asset would be more precise but much noisier
