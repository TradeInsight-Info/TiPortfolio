# GitHub Actions PyPI Publish

**Goal**: Automate PyPI publishing via GitHub Actions triggered on git tag push
**Architecture**: GitHub Actions workflow using PyPI trusted publisher (OIDC) — no API tokens needed
**Tech Stack**: GitHub Actions, `uv build`, `pypa/gh-action-pypi-publish`, OIDC trusted publisher
**Spec**: openspec/changes/github-actions-pypi-publish/specs/

## File Map:

1. Create : `.github/workflows/publish.yml` — publish workflow triggered on version tags
2. Modify : `.github/workflows/ci.yml` — add build verification step (ensure wheel builds before merge)

## Chunks

### Chunk 1: Publish workflow
Create a new workflow that triggers on `v*` tag pushes, builds the wheel, and publishes to PyPI using trusted publisher (OIDC).

Files:
- `.github/workflows/publish.yml`
Steps:
- Step 1: Trigger on `push: tags: ['v*']`
- Step 2: Checkout, setup Python 3.12, install uv
- Step 3: Run tests first (`uv run pytest`)
- Step 4: Build with `uv build`
- Step 5: Publish with `pypa/gh-action-pypi-publish@release/v1` using OIDC (id-token: write)

### Chunk 2: CI build check
Add a build step to the existing CI workflow so broken packaging is caught before merge.

Files:
- `.github/workflows/ci.yml`
Steps:
- Step 1: Add `uv build` step after tests pass
