## Context

TiPortfolio uses `uv` with `[tool.uv] package = true` and a `src/` layout. There's no `[build-system]` section, so `uv build` and `pip install` won't work. The current `pyproject.toml` has all deps as required (including heavy ones like `riskfolio-lib` that are only used by `Weigh.ERC`).

## Goals / Non-Goals

**Goals:**
- Make `uv build` produce a valid wheel
- Make `pip install tiportfolio` work from PyPI
- Split optional heavy deps into extras
- Update README to match current API

**Non-Goals:**
- Not setting up CI/CD for automated publishing (manual `uv publish` for now)
- Not adding a changelog or release notes workflow
- Not changing the version beyond 0.1.0

## Decisions

### 1. Hatchling as build backend
**Decision**: Use `hatchling` — it's the default for modern Python, works well with `src/` layout, and integrates with `uv build`.
**Alternative**: `setuptools` — more complex config for src layout.

### 2. riskfolio-lib as optional
**Decision**: Move to `[project.optional-dependencies] erc = ["riskfolio-lib>=7.0.1"]`. It's a heavy dep (~200MB with scipy/cvxpy) only needed for `Weigh.ERC`.
**Rationale**: Most users won't need ERC; keep the core install lightweight.

### 3. plotly + kaleido as optional
**Decision**: `interactive = ["plotly>=5.0.0", "kaleido"]` — for `plot_interactive()` and PNG export.
**Rationale**: Core `plot()` uses matplotlib (already required). Interactive charts are an extra.

## Risks / Trade-offs

- **[Risk] Package name `tiportfolio` taken on PyPI** → Check with `pip index versions tiportfolio` before publishing
- **[Breaking] riskfolio-lib removal from core** → Document in README: `pip install tiportfolio[erc]`
