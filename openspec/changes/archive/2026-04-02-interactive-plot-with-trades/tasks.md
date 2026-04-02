> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Store prices on _SingleResult

- [x] 1.1 Add `_prices: dict[str, pd.DataFrame] | None = None` parameter to `_SingleResult.__init__` in `src/tiportfolio/result.py`
- [x] 1.2 In `src/tiportfolio/backtest.py`, pass `backtest.data` (the prices dict) into `_SingleResult` when constructing results

## 2. Per-asset equity reconstruction

- [x] 2.1 Add `_per_asset_equity() -> pd.DataFrame` private method on `_SingleResult` that:
    - Extracts (date, ticker, qty_after) from `_trade_records`
    - Pivots to a positions DataFrame indexed by date, one column per ticker
    - Reindexes to match `equity_curve.index` and forward-fills quantities
    - Multiplies each column by `_prices[ticker]["close"]` to get dollar values
    - Returns DataFrame with columns = tickers + "total" (total = equity_curve values)

## 3. Implement plot_interactive()

- [x] 3.1 Add `plot_interactive()` method on `_SingleResult` that returns a Plotly `Figure`
- [x] 3.2 Add one `Scatter` trace per asset from `_per_asset_equity()` with hover template showing date and value
- [x] 3.3 Add a bold total equity `Scatter` trace (thicker line, e.g. width=3) with hover template showing date and total value
- [x] 3.4 Extract buy trades (`delta > 0`) from `_trade_records`, add green upward triangle markers (`marker_symbol="triangle-up"`) positioned on the total equity line at each trade date, with hover template: date, "BUY", ticker, price, quantity
- [x] 3.5 Extract sell trades (`delta < 0`) from `_trade_records`, add red downward triangle markers (`marker_symbol="triangle-down"`) positioned on the total equity line, with hover template: date, "SELL", ticker, price, quantity
- [x] 3.6 Add green dotted vertical lines (`shapes` with `line_dash="dot"`) from y=0 to marker y-value at each buy date
- [x] 3.7 Add red dotted vertical lines from y=0 to marker y-value at each sell date
- [x] 3.8 Set layout: title, axes labels, legend, reasonable default height/width

## 4. Wire up BacktestResult

- [x] 4.1 Add `plot_interactive()` on `BacktestResult` that delegates to `_SingleResult.plot_interactive()` for single results
- [x] 4.2 For multi-backtest (2+ results): render overlaid total equity lines per strategy, each with a distinct colour and labelled by strategy name
- [x] 4.3 For multi-backtest: add buy/sell trade markers per strategy, colour-matched to the strategy's equity line, with hover showing strategy name + date + BUY/SELL + ticker + price + quantity
- [x] 4.4 For multi-backtest: make trade marker traces togglable via Plotly legend (grouped by strategy name)

## 5. Tests

- [x] 5.1 Add test that `_per_asset_equity()` returns correct DataFrame shape and column names
- [x] 5.2 Add test that `plot_interactive()` returns a `plotly.graph_objects.Figure`
- [x] 5.3 Add test that buy/sell markers are present in the figure data traces
- [x] 5.4 Add test that `fig.write_image()` produces a PNG file (skip if kaleido not installed)
- [x] 5.5 Add test that `BacktestResult.plot_interactive()` with multiple results returns a Figure with one equity trace per strategy
- [x] 5.6 Add test that multi-backtest `plot_interactive()` includes trade markers for each strategy

## 6. Update notebooks

- [x] 6.1 In the 5 demo notebooks, use `result[0].plot_interactive()` for single-strategy detailed charts (per-asset + trades)
- [x] 6.2 In the 5 demo notebooks, use `comparison.plot_interactive()` for multi-backtest comparison charts (replaces `comparison.plot()`)
