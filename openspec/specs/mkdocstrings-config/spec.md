# Spec: mkdocstrings-config

## Purpose

Configure the mkdocstrings plugin in `mkdocs.yml` with a Python handler and ensure the navigation references all existing pages without broken links.

## Requirements

### Requirement: mkdocstrings python handler configured
`mkdocs.yml` SHALL configure the mkdocstrings plugin with a python handler specifying rendering options.

#### Scenario: Handler config present
- **WHEN** `mkdocs.yml` is read
- **THEN** the `mkdocstrings` plugin SHALL have a `handlers.python` section with `options` including `show_source: false` and `docstring_style: google`

### Requirement: Nav includes all existing pages
The `mkdocs.yml` nav SHALL reference all existing docs pages without broken links.

#### Scenario: No missing pages
- **WHEN** `mkdocs build` is run
- **THEN** no warnings about missing files SHALL appear

### Requirement: Nav includes cli.md
`docs/cli.md` SHALL be listed in the navigation.

#### Scenario: CLI page in nav
- **WHEN** a user browses the docs
- **THEN** a CLI reference link SHALL be visible in the navigation

### Requirement: Missing usage.md created
`docs/guides/usage.md` SHALL exist to resolve the broken nav reference.

#### Scenario: usage.md exists
- **WHEN** `mkdocs build` is run
- **THEN** `docs/guides/usage.md` SHALL be found without warnings
