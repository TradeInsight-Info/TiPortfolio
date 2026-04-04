# Build CLI for TiPortfolio

**Goal**: Provide a `tiportfolio` command-line interface so users can run backtests without writing Python scripts.
**Architecture**: Single entry point `tiportfolio` with subcommands mapping to rebalance frequencies, plus a generic `run` subcommand for advanced usage.
**Tech Stack**: Python 3.12, `click` (lightweight CLI framework), existing TiPortfolio engine
**Spec**: `openspec/changes/build-cli/specs/`

## Algo Inventory → CLI Mapping

### Signals (frequency subcommands)
| Algo | CLI mapping | Notes |
|---|---|---|
| `Signal.Monthly(day=)` | `tiportfolio monthly` | `--day start/mid/end` |
| `Signal.Quarterly(months=, day=)` | `tiportfolio quarterly` | `--months 1,4,7,10 --day end` |
| `Signal.Weekly(day=)` | `tiportfolio weekly` | `--day start/mid/end` |
| `Signal.Yearly(day=, month=)` | `tiportfolio yearly` | `--day end --month 12` |
| `Signal.EveryNPeriods(n=, period=, day=)` | `tiportfolio every --n 5 --period day` | Generic frequency |
| `Signal.Once()` | `tiportfolio once` | Buy-and-hold |

### Select (--select option)
| Algo | CLI mapping | Notes |
|---|---|---|
| `Select.All()` | `--select all` (default) | Always included |
| `Select.Momentum(n=, lookback=)` | `--select momentum --top-n 3 --lookback 90d` | Requires lookback |
| `Select.Filter(...)` | Not exposed | Requires Python callable |

### Weigh (--ratio option)
| Algo | CLI mapping | Notes |
|---|---|---|
| `Weigh.Equally()` | `--ratio equal` | Default |
| `Weigh.Ratio(weights=)` | `--ratio 0.7,0.2,0.1` | Maps positionally to tickers |
| `Weigh.ERC(lookback=)` | `--ratio erc --lookback 90d` | Risk parity |
| `Weigh.BasedOnHV(...)` | `--ratio hv --target-hv 0.10 --lookback 90d` | Vol-targeting |
| `Weigh.BasedOnBeta(...)` | Not exposed in v1 | Requires base_data arg |

### Config (--config options)
| Field | CLI flag | Default |
|---|---|---|
| `initial_capital` | `--capital 10000` | 10000 |
| `fee_per_share` | `--fee 0.0035` | 0.0035 |
| `risk_free_rate` | `--rf 0.04` | 0.04 |

### Data
| | CLI flag | Notes |
|---|---|---|
| tickers | `--tickers QQQ,BIL,GLD` | Required |
| date range | `--start 2019-01-01 --end 2024-12-31` | Required |
| source | `--source yfinance` | Default yfinance |
| csv dir | `--csv ./data/` | Offline mode |

### Output
| | CLI flag | Notes |
|---|---|---|
| summary | default output | Always printed |
| full summary | `--full` | Extended metrics |
| plot | `--plot output.png` | Save equity chart |
| leverage | `--leverage 1.5` | Post-sim leverage |

## File Map:

1. Create : `src/tiportfolio/cli.py` - Main CLI module with click commands
2. Modify : `pyproject.toml` - Add `[project.scripts]` entry point + click dependency
3. Create : `tests/test_cli.py` - CLI tests using click's CliRunner
4. Modify : `src/tiportfolio/__init__.py` - No change needed (CLI imports from package)

## Chunks

### Chunk 1: CLI scaffold and entry point
Set up the click app, register subcommands, add `[project.scripts]` to pyproject.toml.

Files:
- `src/tiportfolio/cli.py`
- `pyproject.toml`
Steps:
- Create click group `cli` with shared options (--tickers, --start, --end, --source, --csv, --capital, --fee, --rf, --select, --ratio, --leverage, --plot, --full)
- Add subcommands: monthly, quarterly, weekly, yearly, every, once
- Register entry point `tiportfolio = "tiportfolio.cli:cli"` in pyproject.toml
- Add `click` to dependencies

### Chunk 2: Algo construction from CLI args
Parse --ratio, --select, and frequency args into the appropriate Algo instances.

Files:
- `src/tiportfolio/cli.py`
Steps:
- Build Signal from subcommand + --day/--months/--n/--period args
- Build Select from --select + --top-n/--lookback args
- Build Weigh from --ratio (equal → Equally, csv floats → Ratio, erc → ERC, hv → BasedOnHV)
- Compose into Portfolio → Backtest → run()

### Chunk 3: Output formatting
Print summary, optionally save plot, handle --full and --leverage flags.

Files:
- `src/tiportfolio/cli.py`
Steps:
- Print summary() or full_summary() based on --full flag
- Save plot to file if --plot provided
- Apply leverage parameter to run()

### Chunk 4: Tests
Test CLI invocations using click's CliRunner with CSV data for offline testing.

Files:
- `tests/test_cli.py`
Steps:
- Test basic monthly rebalance with ratio
- Test quarterly with equal weights
- Test --leverage flag
- Test --plot flag generates file
- Test --full flag output
- Test invalid inputs (missing tickers, bad ratio format)
