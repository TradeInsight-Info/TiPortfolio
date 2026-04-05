# MkDocs API Docs from Docstrings

**Goal**: Auto-generate API reference pages from Python docstrings using mkdocstrings, while keeping the existing hand-written docs.
**Architecture**: Add `docs/api/reference.md` pages with `:::` directives; configure mkdocstrings handler; fill in missing docstrings.
**Tech Stack**: mkdocs 1.6.1, mkdocs-material, mkdocstrings[python] (already in dev deps)
**Spec**: `openspec/changes/mkdocs-api-docs/specs/`

## Current State
- mkdocs.yml exists with material theme, mkdocstrings plugin declared but **unconfigured**
- `docs/api/index.md` is a thorough hand-written API reference — keep as-is
- Docstring coverage: excellent in algos/, partial in backtest.py, result.py, portfolio.py
- `guides/usage.md` missing but in nav (build-breaking)
- `docs/cli.md` exists but not in nav

## Docstring Gaps to Fill
1. `portfolio.py` — Portfolio.__init__ needs Args block
2. `backtest.py` — Backtest.__init__ needs Args block
3. `result.py` — BacktestResult public methods need Args/Returns
4. `data.py` — validate_data needs Args/Raises

## File Map:

1. Modify : `mkdocs.yml` - Configure mkdocstrings python handler, add reference pages to nav, fix nav issues
2. Create : `docs/api/reference.md` - Auto-generated API reference using ::: directives for all public modules
3. Modify : `src/tiportfolio/portfolio.py` - Add Args docstrings to Portfolio.__init__
4. Modify : `src/tiportfolio/backtest.py` - Add Args docstrings to Backtest.__init__
5. Modify : `src/tiportfolio/result.py` - Add Args/Returns docstrings to BacktestResult public methods
6. Modify : `src/tiportfolio/data.py` - Add Args/Raises to validate_data
7. Create : `docs/guides/usage.md` - Create missing file referenced in nav

## Chunks

### Chunk 1: Fix mkdocs config and nav
Configure mkdocstrings handler, fix missing pages, add cli.md and reference.md to nav.

Files:
- `mkdocs.yml`
- `docs/guides/usage.md`
Steps:
- Add mkdocstrings python handler config (show_source: false, show_root_heading: true, etc.)
- Fix nav: create usage.md stub, add cli.md, add api/reference.md
- Remove offline plugin reference if not in deps

### Chunk 2: Fill docstring gaps
Add Args/Returns blocks to modules with partial coverage.

Files:
- `src/tiportfolio/portfolio.py`, `src/tiportfolio/backtest.py`, `src/tiportfolio/result.py`, `src/tiportfolio/data.py`
Steps:
- Add Google-style Args blocks to constructors and public methods
- Keep existing docstrings, just extend them

### Chunk 3: Create auto-generated reference page
Add docs/api/reference.md with ::: directives for all public modules.

Files:
- `docs/api/reference.md`
Steps:
- Add ::: tiportfolio directives for each public module
- Organize by: Core (Portfolio, Backtest, run, TiConfig), Data, Algos (Signal, Select, Weigh, Action), Results

### Chunk 4: Verify build
Run mkdocs build to confirm everything renders correctly.
