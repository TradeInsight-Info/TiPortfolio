> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [ ]) syntax for tracking.

## 1. Project Setup

- [x] 1.1 Add `click>=8.0` to dependencies in `pyproject.toml`
- [x] 1.2 Add `[project.scripts]` entry point: `tiportfolio = "tiportfolio.cli:cli"`
- [x] 1.3 Run `uv sync` to install click

## 2. Tests First (TDD)

- [x] 2.1 Create `tests/test_cli.py` with tests using click's CliRunner: basic monthly rebalance with explicit ratio, quarterly with equal weights, weekly, yearly, every, once subcommands, --full flag, --leverage single float, --leverage comma-separated list creates multiple backtests, --plot flag generates file, missing tickers error, ratio count mismatch error, --select momentum with --top-n, --ratio erc, --ratio hv with --target-hv
- [x] 2.2 Run tests and confirm they fail (red phase)

## 3. CLI Scaffold

- [x] 3.1 Create `src/tiportfolio/cli.py` with click group `cli`, `shared_options` decorator, and `_parse_lookback()` helper
- [x] 3.2 Implement `_build_select()` — parse --select flag into Select algo (all, momentum)
- [x] 3.3 Implement `_build_weigh()` — parse --ratio flag into Weigh algo (equal, explicit floats, erc, hv)
- [x] 3.4 Implement `_build_csv_map()` — parse --csv directory into dict for fetch_data
- [x] 3.5 Implement `_run_backtest()` — shared runner: fetch data, build Portfolio, Backtest, run(), print output, save plot

## 4. Subcommands

- [x] 4.1 Add `monthly` subcommand with `--day` option (default "end")
- [x] 4.2 Add `quarterly` subcommand with `--months` and `--day` options
- [x] 4.3 Add `weekly` subcommand with `--day` option
- [x] 4.4 Add `yearly` subcommand with `--day` and `--month` options
- [x] 4.5 Add `every` subcommand with required `--n` and `--period` options, plus `--day`
- [x] 4.6 Add `once` subcommand (no extra options)

## 5. Documentation

- [x] 5.1 Create `docs/cli.md` with examples for all subcommands (monthly, quarterly, weekly, yearly, every, once), all --ratio modes (equal, explicit, erc, hv), --select momentum, --leverage (single and list), --plot, --full, --csv offline mode
- [x] 5.2 Add "## CLI" section to `README.md` with 3-4 key examples: monthly with explicit ratio, equal weight quarterly, leverage comparison with --leverage list, and link to docs/cli.md

## 6. Verification

- [x] 6.1 Run all CLI tests and confirm they pass (green phase)
- [x] 6.2 Run full test suite to confirm no regressions
- [x] 6.3 Test manually: `tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio 0.7,0.2,0.1 --csv tests/data/`
- [x] 6.4 Test manually: `tiportfolio monthly --tickers QQQ,BIL,GLD --start 2019-01-01 --end 2024-12-31 --ratio 0.7,0.2,0.1 --leverage 1.0,1.5,2.0 --csv tests/data/`
