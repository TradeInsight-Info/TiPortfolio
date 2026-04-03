## ADDED Requirements

### Requirement: Publish workflow triggered on version tags
A GitHub Actions workflow SHALL publish to PyPI when a version tag is pushed.

#### Scenario: Tag push triggers publish
- **WHEN** a tag matching `v*` (e.g., `v0.1.0`) is pushed to the repository
- **THEN** the publish workflow SHALL run

#### Scenario: Non-tag pushes do not trigger publish
- **WHEN** a regular commit is pushed to any branch
- **THEN** the publish workflow SHALL NOT run

### Requirement: Tests run before publish
The publish workflow SHALL run the test suite before publishing.

#### Scenario: Tests pass before publish
- **WHEN** the publish workflow runs
- **THEN** it SHALL execute `uv run pytest` and only proceed to build/publish if tests pass

#### Scenario: Tests fail stops publish
- **WHEN** tests fail during the publish workflow
- **THEN** the workflow SHALL fail and NOT publish to PyPI

### Requirement: Build and publish via OIDC trusted publisher
The workflow SHALL use PyPI trusted publisher (OIDC) for authentication — no API tokens stored in secrets.

#### Scenario: Wheel built and uploaded
- **WHEN** tests pass
- **THEN** the workflow SHALL build the wheel with `uv build` and upload to PyPI using `pypa/gh-action-pypi-publish`

#### Scenario: OIDC permissions configured
- **WHEN** the publish job runs
- **THEN** it SHALL have `id-token: write` and `contents: read` permissions for OIDC

### Requirement: CI build verification
The existing CI workflow SHALL verify the package builds correctly on every PR.

#### Scenario: Build check on PR
- **WHEN** CI runs on a pull request
- **THEN** it SHALL run `uv build` after tests to verify the wheel builds successfully
