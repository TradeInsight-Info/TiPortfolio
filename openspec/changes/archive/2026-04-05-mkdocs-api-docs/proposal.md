## Why

The project has mkdocs and mkdocstrings[python] in dev dependencies but doesn't use mkdocstrings auto-generation anywhere. The API reference (`docs/api/index.md`) is entirely hand-written, meaning it drifts from the code. The algos already have excellent Google-style docstrings — we should let mkdocstrings render them into browsable API docs automatically.

## What Changes

- Configure mkdocstrings python handler in `mkdocs.yml`
- Create `docs/api/reference.md` with `:::` auto-doc directives for all public modules
- Fill missing Args/Returns docstring blocks in portfolio.py, backtest.py, result.py, data.py
- Fix mkdocs nav: add cli.md, add reference.md, create missing usage.md stub
- Verify `mkdocs build` succeeds

## Capabilities

### New Capabilities
- `mkdocstrings-config`: Configure mkdocstrings python handler and fix mkdocs.yml nav
- `api-reference-autodoc`: Auto-generated API reference page using ::: directives
- `docstring-completion`: Fill missing Args/Returns blocks in public APIs

### Modified Capabilities
<!-- None — existing hand-written docs preserved as-is -->

## Impact

- **Code**: Docstring additions only (no behavior changes)
- **Docs**: New `docs/api/reference.md`, updated `mkdocs.yml`, new `docs/guides/usage.md` stub
- **Dependencies**: None (mkdocstrings already in dev deps)
