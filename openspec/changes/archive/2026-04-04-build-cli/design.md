## Context

TiPortfolio is a Python library with no CLI. Users write scripts for every backtest. The algo system (Signal, Select, Weigh, Action) has a clean decomposition that maps naturally to CLI flags. Adding a CLI layer will make the library more accessible without changing the core API.

## Goals / Non-Goals

**Goals:**
- `tiportfolio` command callable after `pip install tiportfolio`
- Frequency as subcommand (monthly, quarterly, weekly, yearly, every, once)
- Common flags for tickers, dates, weighting, selection, config, output
- Offline CSV mode for testing and CI
- Minimal code — thin wrapper that composes existing algos

**Non-Goals:**
- Interactive mode or REPL
- Multi-backtest comparison from CLI (single backtest per invocation)
- Exposing algos that require Python callables (VIX, Indicator, Filter, BasedOnBeta)
- Custom algo composition beyond what flags support

## Decisions

### Decision 1: Click over argparse/typer

**Chosen**: `click` — lightweight, widely adopted, built-in test runner (`CliRunner`), good subcommand support.

**Alternative**: `typer` — more "modern" but adds pydantic dependency. `argparse` — stdlib but verbose and poor subcommand UX.

**Rationale**: Click is already battle-tested, has excellent testing support, and doesn't pull in heavy dependencies.

### Decision 2: Shared options via decorator

All subcommands share the same options (tickers, dates, config, etc.). Use a `shared_options` decorator to apply them consistently:

```python
def shared_options(f):
    """Apply all shared CLI options to a subcommand."""
    f = click.option("--tickers", required=True, help="Comma-separated tickers")(f)
    f = click.option("--start", required=True, help="Start date YYYY-MM-DD")(f)
    f = click.option("--end", required=True, help="End date YYYY-MM-DD")(f)
    f = click.option("--ratio", default="equal", help="Weighting: equal, 0.7,0.2,0.1, erc, hv")(f)
    f = click.option("--select", "select_", default="all", help="Selection: all, momentum")(f)
    # ... more options
    return f

@cli.command()
@shared_options
def monthly(day, **kwargs):
    signal = Signal.Monthly(day=day)
    _run_backtest(signal, **kwargs)
```

This keeps each subcommand body to ~3 lines (build signal, call shared runner).

### Decision 3: Single `_run_backtest()` helper

All subcommands call a shared `_run_backtest(signal, **kwargs)` function that:
1. Parses tickers, builds data via `fetch_data()`
2. Builds Select algo from `--select`
3. Builds Weigh algo from `--ratio`
4. Composes Portfolio → Backtest → `run(leverage=)`
5. Prints summary/full_summary, saves plot if requested

This avoids duplicating logic across 6 subcommands.

### Decision 4: --ratio parsing strategy

The `--ratio` value is a string parsed as:
- `"equal"` → `Weigh.Equally()`
- `"erc"` → `Weigh.ERC(lookback=...)`
- `"hv"` → `Weigh.BasedOnHV(initial_ratio=equal, target_hv=..., lookback=...)`
- Otherwise → split by `,`, parse as floats, zip with tickers → `Weigh.Ratio({...})`

### Decision 5: --lookback parsing

`--lookback` accepts strings like `90d`, `6m`, `1y` and converts to `pd.DateOffset`:
- `Nd` → `pd.DateOffset(days=N)`
- `Nm` → `pd.DateOffset(months=N)`
- `Ny` → `pd.DateOffset(years=N)`

Default: `60d` (used by ERC and HV when not specified).

### Decision 6: --leverage accepts float or comma-separated list

`--leverage 1.5` applies a single leverage factor. `--leverage 1.0,1.5,2.0` creates N identical backtests (one per factor) and calls `run(bt1, bt2, ..., leverage=[1.0, 1.5, 2.0])` for side-by-side comparison. This reuses the leverage list support added in the `add-leverage-parameter` change. Each backtest gets a name suffix like `"portfolio (1.5x)"`.

### Decision 7: --csv accepts a directory

`--csv ./tests/data/` scans the directory for `<ticker>.csv` or `<ticker>_*.csv` files, building a dict for `fetch_data(csv=...)`. This keeps the CLI simple — no need to specify per-ticker paths.

### Decision 8: Documentation in docs/cli.md + README section

`docs/cli.md` provides comprehensive examples covering all subcommands and options. `README.md` gets a concise "## CLI" section with 3-4 key examples (monthly with ratio, equal weight, leverage comparison) plus a link to the full docs page.

## Risks / Trade-offs

- **Click adds a dependency** → Acceptable; click is small (~80KB) and widely used. It's already a transitive dep of many tools.
- **Limited algo coverage** → By design; algos requiring Python callables can't be expressed as CLI flags. Users who need those use the Python API. The CLI covers the 80% case.
- **Single backtest per invocation** → Exception: `--leverage 1.0,1.5,2.0` creates multiple backtests for leverage comparison. Other multi-backtest scenarios can be added later.
- **--ratio overloading** → One flag serves multiple weighting strategies. Could confuse users. Mitigated by clear help text and examples in `--help`.
