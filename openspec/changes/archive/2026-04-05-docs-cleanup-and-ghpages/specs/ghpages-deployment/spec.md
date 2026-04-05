## ADDED Requirements

### Requirement: GitHub Actions workflow for docs deployment
A `.github/workflows/docs.yml` workflow SHALL deploy mkdocs to GitHub Pages on push to master.

#### Scenario: Docs deploy on push to master
- **WHEN** code is pushed to the `master` branch
- **THEN** the workflow SHALL run `mkdocs gh-deploy` to publish to GitHub Pages

#### Scenario: Workflow uses uv and Python 3.12
- **WHEN** the workflow runs
- **THEN** it SHALL use `actions/setup-python@v5` with Python 3.12 and `astral-sh/setup-uv@v4` for dependency management

#### Scenario: Workflow only triggers on doc-relevant changes
- **WHEN** only non-doc files change (e.g., tests/)
- **THEN** the workflow SHOULD still run (simpler than path filtering for correctness)
