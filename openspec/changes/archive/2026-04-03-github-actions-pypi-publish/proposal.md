## Why

Manual `uv publish` requires PyPI tokens and a developer's machine. Automating via GitHub Actions with trusted publisher (OIDC) eliminates token management, ensures every release is built from a clean CI environment, and makes publishing as simple as `git tag v0.1.0 && git push --tags`.

## What Changes

- New `.github/workflows/publish.yml` — triggered on `v*` tag push, runs tests, builds wheel, publishes to PyPI via OIDC trusted publisher
- Modified `.github/workflows/ci.yml` — adds `uv build` step to verify packaging on every PR

## Capabilities

### New Capabilities
- `ci-pypi-publish`: GitHub Actions workflow for automated PyPI publishing on tag push with OIDC trusted publisher

### Modified Capabilities

_(none)_

## Impact

- **New files**: `.github/workflows/publish.yml`
- **Modified files**: `.github/workflows/ci.yml`
- **GitHub settings required**: Configure PyPI trusted publisher for this repo (one-time setup on pypi.org)
