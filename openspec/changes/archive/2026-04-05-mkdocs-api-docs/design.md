## Context

mkdocs and mkdocstrings[python] are already in dev dependencies. The mkdocstrings plugin is declared in mkdocs.yml but has no handler configuration. All API docs are hand-written. The algos modules have excellent docstrings, but core modules (Portfolio, Backtest, BacktestResult) have gaps.

## Goals / Non-Goals

**Goals:**
- Configure mkdocstrings python handler properly
- Create auto-generated reference page alongside existing hand-written API docs
- Fill docstring gaps so mkdocstrings renders complete documentation
- Fix broken nav references

**Non-Goals:**
- Replacing the hand-written `docs/api/index.md` (it stays as the primary API guide)
- Adding docstrings to private/internal functions
- Changing mkdocs theme or layout

## Decisions

### Decision 1: Separate reference page, keep hand-written API guide

**Chosen**: Create `docs/api/reference.md` for auto-generated docs. Keep `docs/api/index.md` as-is.

**Rationale**: The hand-written guide has examples and explanations that mkdocstrings can't generate. The auto-generated page serves as a complete, always-current reference. Users choose which they prefer.

### Decision 2: One reference page with sections (not per-module pages)

**Chosen**: Single `reference.md` with sections for Core, Data, Signals, Selection, Weighting, Actions, Results.

**Alternative**: One page per module (reference/portfolio.md, reference/backtest.md, etc.)

**Rationale**: The public API is small enough for one page. Fewer files = easier maintenance.

### Decision 3: mkdocstrings handler options

```yaml
plugins:
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
          options:
            docstring_style: google
            show_source: false
            show_root_heading: true
            show_root_full_path: false
            members_order: source
```

Key choices:
- `paths: [src]` — tells mkdocstrings where to find the package
- `show_source: false` — keeps pages clean (users can go to GitHub for source)
- `docstring_style: google` — matches project convention (CLAUDE.md)
- `members_order: source` — preserves logical ordering from source files

### Decision 4: Minimal docstring additions

Only add Args/Returns blocks to public API symbols that mkdocstrings will render. Don't touch private functions or internal modules. Keep additions consistent with existing Google-style format.

## Risks / Trade-offs

- **Auto-generated docs may diverge from hand-written docs** → Acceptable; they serve different purposes (reference vs guide)
- **mkdocs build may surface other warnings** → Fix only the known issues (missing usage.md, offline plugin)
