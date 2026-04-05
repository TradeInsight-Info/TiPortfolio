## Context

A comprehensive audit of `docs/` found 23 inconsistencies ranging from wrong function names to missing features. The project has GitHub Actions for CI and PyPI publishing but no docs deployment.

## Goals / Non-Goals

**Goals:**
- Fix all documented inconsistencies
- Add GitHub Pages deployment workflow
- Ensure `mkdocs build` succeeds without warnings (except pre-existing non-nav ones)

**Non-Goals:**
- Rewriting docs from scratch (fix in place)
- Adding new guide content beyond what's needed to fix issues
- Versioned docs (mike) — out of scope

## Decisions

### Decision 1: Fix in-place rather than rewrite

**Rationale**: The existing docs are well-structured. Most issues are parameter names, function names, or missing entries — surgical fixes are sufficient.

### Decision 2: GitHub Pages via mkdocs gh-deploy

**Chosen**: Use `mkdocs gh-deploy --force` in a GitHub Actions workflow. This pushes the built site to the `gh-pages` branch.

**Alternative**: GitHub's built-in Pages from a `docs/` folder on `master`. But mkdocs needs to build first (it generates `site/`), so a workflow is required.

### Decision 3: Workflow on every push to master

Rather than path-filtering (only `docs/**`), run on every master push. Docs may reference code (via mkdocstrings), so code changes can affect rendered docs. Simple and safe.

## Risks / Trade-offs

- **about.md broken links**: The links point to `dimensions/` files that were never created. Best fix: remove the dead links or point to the guides that replaced them.
- **api/index.md is large**: Many fixes needed. Risk of introducing new errors. Mitigate: verify with `mkdocs build` and spot-check rendered output.
