## ADDED Requirements

### Requirement: Build system configuration
The project SHALL have a `[build-system]` section in `pyproject.toml` using `hatchling` as the build backend.

#### Scenario: Build produces wheel
- **WHEN** `uv build` is run from the project root
- **THEN** a `.whl` file SHALL be produced in `dist/` containing the `tiportfolio` package

#### Scenario: Wheel contains all source files
- **WHEN** the wheel is inspected
- **THEN** it SHALL contain all `.py` files from `src/tiportfolio/` including subpackages (`algos/`, `helpers/`)

### Requirement: Package metadata
The `pyproject.toml` SHALL have complete PyPI metadata.

#### Scenario: Classifiers present
- **WHEN** the package is built
- **THEN** it SHALL include classifiers for: Python 3.10-3.12, License (Apache-2.0), Topic (Finance, Trading)

#### Scenario: Optional dependencies defined
- **WHEN** a user runs `pip install tiportfolio[interactive]`
- **THEN** `plotly` and `kaleido` SHALL be installed

#### Scenario: ERC optional dependency
- **WHEN** a user runs `pip install tiportfolio[erc]`
- **THEN** `riskfolio-lib` SHALL be installed

### Requirement: Installable and importable
The published package SHALL be installable and importable in any Python 3.10+ environment.

#### Scenario: Fresh install and import
- **WHEN** `pip install tiportfolio` is run in a clean environment
- **THEN** `import tiportfolio as ti` SHALL work and expose the public API

### Requirement: PEP 561 type marker
The package SHALL include a `py.typed` marker for type checking support.

#### Scenario: py.typed exists
- **WHEN** the wheel is inspected
- **THEN** `tiportfolio/py.typed` SHALL be present

### Requirement: README reflects current API
The README SHALL show correct code examples using the current simplified API.

#### Scenario: Quick start example works
- **WHEN** a user copies the Quick Start code from README
- **THEN** it SHALL use `ti.Signal.Monthly()`, `ti.Select.All()`, `ti.Weigh.Equally()`, `ti.Action.Rebalance()` (not the old API)

### Requirement: PyPI publication
The package SHALL be published to PyPI.

#### Scenario: Successful upload
- **WHEN** `uv publish` is run with valid credentials
- **THEN** the package SHALL be available at `pypi.org/project/tiportfolio/`
