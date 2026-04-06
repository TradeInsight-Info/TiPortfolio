# CLI AIP Support

**Goal**: Add `--aip` option to the CLI so users can simulate auto investment plans from the terminal without writing Python.
**Architecture**: Add a shared `--aip` option to all existing subcommands. When provided, `_run_backtest()` calls `ti.run_aip()` instead of `ti.run()`.
**Tech Stack**: Python, Click (existing CLI framework), existing `run_aip()` function
**Spec**: `openspec/specs/cli-aip/spec.md`

## File Map:

1. Modify : `src/tiportfolio/cli.py` - Add `--aip` shared option and route to `run_aip()` when set
2. Create : `tests/test_cli_aip.py` - CLI tests for `--aip` flag
3. Modify : `docs/cli.md` - Document `--aip` option (if exists)

## Chunks

### Chunk 1: Add --aip option to CLI
Small change: add `--aip` to `shared_options`, pass it through to `_run_backtest`, and call `ti.run_aip()` when non-zero.

Files:
- `src/tiportfolio/cli.py`
Steps:
- Step 1: Add `--aip` option (float, default None) to `shared_options` decorator
- Step 2: Accept `aip` param in `_run_backtest()`, call `ti.run_aip()` when provided
- Step 3: Handle leverage + AIP combination

### Chunk 2: Tests
Files:
- `tests/test_cli_aip.py`
Steps:
- Step 1: Test `tiportfolio monthly --aip 1000 --tickers ... --start ... --end ...` produces output with contribution metrics
- Step 2: Test that `--aip` works with other subcommands (quarterly, once, etc.)
- Step 3: Test that omitting `--aip` produces normal output (no contribution rows)
