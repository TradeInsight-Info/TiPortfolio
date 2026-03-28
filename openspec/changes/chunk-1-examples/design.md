## Context

Chunk 1 provides: `fetch_data`, `Portfolio`, `Signal.Monthly`, `Select.All`, `Weigh.Equally`, `Action.Rebalance`, `Action.PrintInfo`, `Backtest`, `run`, `TiConfig`, `summary()`, `plot()`. All leaf-only, equal-weight, monthly rebalance. Examples must stay within this scope.

## Goals / Non-Goals

**Goals:**
- 5 runnable examples covering different allocation patterns
- Each file is self-contained — copy-paste and run
- Progressive complexity: simplest first, advanced last

**Non-Goals:**
- Examples using Chunk 2+ features (Ratio, Momentum, branching, VIX, trees)
- Jupyter notebooks (deferred)
- Performance benchmarks

## Decisions

### Each example fetches its own data
**Why:** Self-contained — users don't need to set up fixtures or share state between files.

### Examples use 5-year date range (2019-2024)
**Why:** Long enough to see meaningful returns and drawdowns. Covers COVID crash (March 2020) which makes results interesting.

### No matplotlib.show() — save to file instead
**Decision:** Examples call `plot()` to get the figure, then `fig.savefig()` to a PNG. This works in headless environments and doesn't block on a GUI window.

## Risks / Trade-offs

- **[Risk] yfinance rate limits** → Examples print a note about potential download delays
- **[Risk] Price data changes over time** → Summary values in comments are approximate, not assertions
