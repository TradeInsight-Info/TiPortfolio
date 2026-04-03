# PyPI Release for TiPortfolio

**Goal**: Package TiPortfolio as a distributable Python package and publish to PyPI
**Architecture**: Standard Python packaging with `hatchling` build backend, `uv build` for building, `twine` for upload
**Tech Stack**: pyproject.toml (PEP 621), hatchling, twine, PyPI
**Spec**: openspec/changes/pypi-release/specs/

## File Map:

1. Modify : `pyproject.toml` — Add `[build-system]`, refine metadata, classifiers, optional deps
2. Modify : `README.md` — Update code examples to match current API (Signal/Select/Weigh/Action)
3. Create : `src/tiportfolio/py.typed` — PEP 561 marker for type checking support
4. Verify : `LICENSE` — Ensure Apache-2.0 is correct and complete

## Chunks

### Chunk 1: Fix pyproject.toml for building
Add `[build-system]` with hatchling, update classifiers, add optional dependencies group (plotly, kaleido), fix version.

Files:
- `pyproject.toml`
Steps:
- Step 1: Add `[build-system] requires = ["hatchling"] build-backend = "hatchling.build"`
- Step 2: Add `[tool.hatch.build.targets.wheel] packages = ["src/tiportfolio"]`
- Step 3: Update classifiers for PyPI (license, python versions, topic)
- Step 4: Add `[project.optional-dependencies] interactive = ["plotly>=5.0.0", "kaleido"]`
- Step 5: Trim heavy optional deps from core — riskfolio-lib should be optional

### Chunk 2: Update README
Fix the Quick Start code example to use the current API (`ti.Signal.Monthly()`, etc. not the old `ti.algo.ScheduleMonthly()`).

Files:
- `README.md`
Steps:
- Step 1: Update code example to use current API
- Step 2: Add installation instructions (`pip install tiportfolio`)

### Chunk 3: Build and test locally
Build the package with `uv build`, verify the wheel installs and imports correctly.

Files:
- (no files — build + verify commands)
Steps:
- Step 1: `uv build` → produces `dist/tiportfolio-0.1.0-py3-none-any.whl`
- Step 2: Install in temp venv and verify `import tiportfolio as ti; print(ti.__all__)`

### Chunk 4: Publish to PyPI
Upload using `twine` or `uv publish`.

Files:
- (no files — publish commands)
Steps:
- Step 1: `uv publish` or `twine upload dist/*`
- Step 2: Verify on pypi.org/project/tiportfolio/
