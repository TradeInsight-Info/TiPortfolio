# Docs Cleanup + GitHub Pages Deployment

**Goal**: Fix all documentation inconsistencies and add GitHub Actions workflow to deploy docs to GitHub Pages.
**Architecture**: Fix docs in-place, add `.github/workflows/docs.yml` for mkdocs gh-deploy.
**Tech Stack**: mkdocs, mkdocs-material, GitHub Pages, GitHub Actions
**Spec**: `openspec/changes/docs-cleanup-and-ghpages/specs/`

## Audit Summary (23 issues found)

### Critical (must fix)
1. `docs/index.md` — `ti.run_backtest()` → should be `ti.run()`; `fee_per_share` not a Backtest param; trade records table schema wrong; summary output schema wrong
2. `docs/api/index.md` — `run()` missing `leverage` param; `next_trading_day` should be `closest_trading_day`; summary table wrong keys; `plot()` default wrong; `plot_histogram`/`plot_security_weights` don't have `interactive` param; missing Signal.Weekly/Yearly/Once/EveryNPeriods/Indicator; missing `csv` on fetch_data
3. `docs/api/structure.md` — `branching.py` doesn't exist; `run_backtest()` should be `run()`; `Context.selected_child` doesn't exist

### Important
4. `docs/api/index.md` — `result.trades` on BacktestResult (only on _SingleResult); CLI not mentioned
5. `docs/guides/comparing-results.md` — `target_hv=60` should be `0.60`
6. `docs/about.md` — broken links to dimensions/ directory

### Minor
7. `docs/guides/fix-time-rebalance.md` — `next_trading_day` wrong param name
8. `docs/guides/allocation-strategies.md` — typo "Voaltility"

## File Map:

1. Modify : `docs/index.md` - Fix function names, Backtest constructor, trade/summary tables
2. Modify : `docs/api/index.md` - Fix run() sig, param names, summary table, add missing signals, add leverage, add csv, fix plot signatures
3. Modify : `docs/api/structure.md` - Remove branching.py, fix run_backtest→run, fix Context fields
4. Modify : `docs/about.md` - Fix broken dimension links
5. Modify : `docs/guides/fix-time-rebalance.md` - Fix next_trading_day→closest_trading_day
6. Modify : `docs/guides/comparing-results.md` - Fix target_hv=60→0.60
7. Modify : `docs/guides/allocation-strategies.md` - Fix "Voaltility" typo
8. Create : `.github/workflows/docs.yml` - GitHub Actions to deploy mkdocs to GitHub Pages

## Chunks

### Chunk 1: Fix critical doc issues
Fix index.md, api/index.md, api/structure.md — the most impactful fixes.

### Chunk 2: Fix minor doc issues
Fix about.md, guides/*.md — smaller fixes.

### Chunk 3: GitHub Pages workflow
Create .github/workflows/docs.yml that runs mkdocs gh-deploy on push to master.
