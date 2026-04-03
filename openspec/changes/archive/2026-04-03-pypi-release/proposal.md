## Why

TiPortfolio has a working API on the `simplify` branch with 20 example scripts, 5 demo notebooks, and 264 passing tests — but it's not installable via `pip`. Users must clone the repo and use `uv run` from the project directory. Publishing to PyPI makes TiPortfolio installable anywhere with `pip install tiportfolio` and discoverable by the Python community.

## What Changes

- Add `[build-system]` to `pyproject.toml` with `hatchling` backend
- Add hatch wheel config to package from `src/tiportfolio`
- Expand classifiers for PyPI discoverability (license, Python versions, topics)
- Add optional dependency groups: `interactive` (plotly, kaleido) and `erc` (riskfolio-lib)
- Move `riskfolio-lib` from core deps to optional (it's only used by `Weigh.ERC`)
- Add `src/tiportfolio/py.typed` marker for PEP 561 type checking support
- Update `README.md` code examples to match current API
- Build with `uv build` and publish with `uv publish`

## Capabilities

### New Capabilities
- `pypi-packaging`: Build system, metadata, optional deps, py.typed, and PyPI publish workflow

### Modified Capabilities

_(none)_

## Impact

- **Modified files**: `pyproject.toml`, `README.md`
- **New files**: `src/tiportfolio/py.typed`
- **Dependencies**: `hatchling` added as build dep; `riskfolio-lib` moved to optional
- **Breaking**: Users who depend on `riskfolio-lib` via `pip install tiportfolio` will need `pip install tiportfolio[erc]`
