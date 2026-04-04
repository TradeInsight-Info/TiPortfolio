## ADDED Requirements

### Requirement: CLI documentation page
A `docs/cli.md` file SHALL document the CLI with usage examples covering all subcommands and key options.

#### Scenario: docs/cli.md exists with examples
- **WHEN** a user opens `docs/cli.md`
- **THEN** it SHALL contain examples for: monthly, quarterly, weekly, yearly, every, once subcommands, --ratio (equal, explicit, erc, hv), --select momentum, --leverage (single and list), --plot, --full, --csv offline mode

### Requirement: README CLI section
The `README.md` SHALL include a CLI section with installation and basic usage examples.

#### Scenario: README has CLI section
- **WHEN** a user reads `README.md`
- **THEN** it SHALL contain a "## CLI" section with at least 3 examples showing monthly rebalance with explicit ratio, equal weight, and leverage comparison
