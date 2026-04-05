## Why

A full audit of `docs/` revealed 23 inconsistencies between the documentation and the actual codebase — including wrong function names (`run_backtest` vs `run`), incorrect parameter names, missing features (leverage, CLI, new signals), and fictional output schemas. Additionally, docs have no automated deployment — they need a GitHub Actions workflow to publish to GitHub Pages.

## What Changes

- Fix all 23 documentation inconsistencies across 7 files
- Add `.github/workflows/docs.yml` for automatic GitHub Pages deployment on push to master

## Capabilities

### New Capabilities
- `docs-consistency-fixes`: Fix all identified inconsistencies in docs/ files
- `ghpages-deployment`: GitHub Actions workflow for mkdocs gh-deploy

### Modified Capabilities
<!-- No code changes — docs only -->

## Impact

- **Docs**: 7 files updated with corrections
- **CI**: New `.github/workflows/docs.yml`
- **Code**: No source code changes
