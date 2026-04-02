## Why

The current `result.plot()` only shows a single total portfolio equity line with a matplotlib chart. Users analyzing strategies in notebooks need to see **per-asset value breakdown** and **trade execution points** to understand when and why the portfolio changes. An interactive Plotly chart with hover tooltips and buy/sell markers makes this immediately visible — while still supporting PNG export for reports and documentation.

## What Changes

- Add a new `plot_interactive()` method on `_SingleResult` that renders a Plotly chart with:
  - One line per asset (position value = qty × price) plus a total portfolio equity line
  - Green up-triangle markers on buy dates with dotted vertical lines
  - Red down-triangle markers on sell dates with dotted vertical lines
  - Hover tooltips showing date + value on lines, and date + buy/sell + price + quantity on trade markers
- Store `prices` data on `_SingleResult` so per-asset equity can be reconstructed from trade records
- Add `.to_png()` / `write_image()` support via Plotly's static export for saving PNG files

## Capabilities

### New Capabilities
- `interactive-portfolio-chart`: Interactive Plotly chart showing per-asset equity curves, total portfolio value, and buy/sell trade markers with hover tooltips and PNG export support

### Modified Capabilities

_(none)_

## Impact

- **Modified files**: `src/tiportfolio/result.py` (add `plot_interactive()` method, store prices data), `src/tiportfolio/backtest.py` (pass prices into `_SingleResult`)
- **Dependencies**: `plotly` (already optional dependency, used by `_render_plotly`), `kaleido` for PNG export (new optional dep)
- **Backwards compatible**: Existing `plot()` method unchanged; new `plot_interactive()` is additive
