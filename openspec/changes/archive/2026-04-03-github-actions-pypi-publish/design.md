## Context

The project has a CI workflow (`.github/workflows/ci.yml`) that runs tests on push to master and PRs. There is no publish workflow. The `pyproject.toml` now has a `[build-system]` with hatchling, so `uv build` produces a valid wheel.

## Goals / Non-Goals

**Goals:**
- Automated PyPI publish on `v*` tag push
- OIDC trusted publisher (no stored API tokens)
- Test gate before publishing
- Build verification in CI

**Non-Goals:**
- Not setting up TestPyPI (publish directly to production PyPI)
- Not automating version bumping (user manually sets version in pyproject.toml and tags)
- Not adding changelog generation

## Decisions

### 1. OIDC trusted publisher over API tokens
**Decision**: Use `pypa/gh-action-pypi-publish` with OIDC trusted publisher.
**Rationale**: No secrets to manage. PyPI verifies the GitHub Actions OIDC token directly. More secure than storing long-lived API tokens in GitHub secrets.
**Setup required**: One-time configuration on pypi.org → "Add a new publisher" → GitHub Actions, set repo owner/name/workflow/environment.

### 2. Separate workflow file
**Decision**: New `.github/workflows/publish.yml` rather than adding a job to `ci.yml`.
**Rationale**: Publish has different triggers (tags only) and permissions (id-token: write). Keeping it separate avoids giving OIDC permissions to regular CI runs.

### 3. Environment protection
**Decision**: Use a `pypi` environment in the publish job for additional protection.
**Rationale**: GitHub environments can require manual approval, adding a safety gate before publishing.

## Risks / Trade-offs

- **[Risk] Trusted publisher not configured on PyPI** → First publish will fail; document the one-time setup steps
- **[Risk] Tag pushed without version bump** → Publish will succeed but upload the wrong version; user must update `pyproject.toml` version before tagging
