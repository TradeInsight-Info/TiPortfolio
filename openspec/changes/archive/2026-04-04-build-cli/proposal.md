## Why

TiPortfolio currently requires writing Python scripts for every backtest. A CLI would let users run common strategies with a single terminal command — faster iteration, lower barrier to entry, and useful for scripting/CI pipelines. The library already has a rich set of algos that map naturally to command-line flags.

## What Changes

- Add `tiportfolio` CLI entry point with subcommands for each rebalance frequency: `monthly`, `quarterly`, `weekly`, `yearly`, `every`, `once`
- Expose selection strategies via `--select` (all, momentum)
- Expose weighting strategies via `--ratio` (equal, explicit weights, erc, hv)
- Support data options: `--tickers`, `--start`, `--end`, `--source`, `--csv`
- Support config overrides: `--capital`, `--fee`, `--rf`
- Support output options: `--full`, `--plot`, `--leverage` (single float or comma-separated list for multi-leverage comparison)
- Create `docs/cli.md` with comprehensive CLI examples
- Add CLI section to `README.md`
- Add `click` as a project dependency
- Register `[project.scripts]` entry point in `pyproject.toml`

## Capabilities

### New Capabilities
- `cli-entry-point`: CLI app scaffold, click group, entry point registration, shared options
- `cli-signal-subcommands`: Subcommands mapping to Signal algos (monthly, quarterly, weekly, yearly, every, once)
- `cli-select-options`: --select flag mapping to Select algos (all, momentum)
- `cli-weigh-options`: --ratio flag mapping to Weigh algos (equal, explicit, erc, hv)
- `cli-data-config`: --tickers, --start, --end, --source, --csv, --capital, --fee, --rf flags
- `cli-output`: Summary printing, --full, --plot, --leverage (float or list) output handling
- `cli-docs`: CLI documentation in docs/cli.md and README.md CLI section

### Modified Capabilities
<!-- None — this is a new CLI layer on top of existing library. No existing specs change. -->

## Impact

- **Code**: New `src/tiportfolio/cli.py` module (~200-300 lines), new `tests/test_cli.py`, new `docs/cli.md`
- **API**: No changes to Python API — CLI is a consumer of the existing API
- **Dependencies**: Adds `click` to project dependencies
- **Build**: Adds `[project.scripts]` entry point to `pyproject.toml`
