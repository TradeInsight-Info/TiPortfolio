# TiPortfolio Implementation Work Plan

The full library scope is split into 5 chunks, each producing a working vertical slice — something you can import, run, and see output from.

## Chunks

| # | Name | Depends On | Deliverable |
|---|------|------------|-------------|
| 1 | [Foundation + Simplest Backtest](./chunk-1-foundation.md) | — | Quick Example runs end-to-end |
| 2 | [More Algos + Branching](./chunk-2-algos-branching.md) | Chunk 1 | fix-time-rebalance.md examples work |
| 3 | [Tree Portfolios + Short Selling](./chunk-3-trees-shorts.md) | Chunk 2 | Dollar-neutral and VIX regime-switching work |
| 4 | [Advanced Weighting](./chunk-4-advanced-weighting.md) | Chunk 3 | Beta Neutral and ERC examples work |
| 5 | [Full Results + Charting](./chunk-5-results-charting.md) | Chunk 1 | All result/charting methods work |

## Dependency Graph

```
Chunk 1 (Foundation)
  ├── Chunk 2 (Algos + Branching)
  │     └── Chunk 3 (Trees + Shorts)
  │           └── Chunk 4 (Advanced Weighting)
  └── Chunk 5 (Results + Charting)  ← can start after Chunk 1
```

## Spec Reference

All chunks implement against the approved spec:
`docs/superpowers/specs/2026-03-28-core-engine-implementation-design.md`
