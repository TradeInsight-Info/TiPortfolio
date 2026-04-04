## Purpose

Defines the CLI package entry point, its dependency on Click, and the shared option group architecture that all subcommands inherit.

## Requirements

### Requirement: CLI entry point registered
The package SHALL register a `tiportfolio` console script entry point in `pyproject.toml` pointing to `tiportfolio.cli:cli`.

#### Scenario: Entry point is callable
- **WHEN** the package is installed
- **THEN** running `tiportfolio --help` SHALL display usage information

### Requirement: Click dependency added
The project SHALL include `click>=8.0` in its dependencies.

#### Scenario: Click is importable
- **WHEN** the package is installed
- **THEN** `import click` SHALL succeed

### Requirement: CLI group with shared options
The CLI SHALL be a click group where shared options are defined once and inherited by all subcommands.

#### Scenario: Shared options available on all subcommands
- **WHEN** `tiportfolio monthly --help` is run
- **THEN** the help SHALL show shared options: `--tickers`, `--start`, `--end`, `--source`, `--csv`, `--capital`, `--fee`, `--rf`, `--select`, `--ratio`, `--leverage`, `--plot`, `--full`
