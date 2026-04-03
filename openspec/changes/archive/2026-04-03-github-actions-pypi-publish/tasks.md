> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Create publish workflow

- [x] 1.1 Create `.github/workflows/publish.yml` with trigger on `push: tags: ['v*']`
- [x] 1.2 Add `test` job: checkout, setup Python 3.12, install uv, `uv sync`, `uv run pytest`
- [x] 1.3 Add `publish` job (depends on `test`): checkout, setup Python 3.12, install uv, `uv build`
- [x] 1.4 Add `pypa/gh-action-pypi-publish@release/v1` step with `packages-dir: dist/`
- [x] 1.5 Set permissions: `id-token: write`, `contents: read` on the publish job
- [x] 1.6 Set environment: `pypi` on the publish job for protection rules

## 2. Update CI workflow

- [x] 2.1 Add `uv build` step after tests in `.github/workflows/ci.yml` to verify packaging
