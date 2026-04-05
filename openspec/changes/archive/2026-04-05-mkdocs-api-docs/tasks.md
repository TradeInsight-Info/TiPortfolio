> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [x]) syntax for tracking.

## 1. Fix mkdocs.yml Config

- [x] 1.1 Configure mkdocstrings python handler in `mkdocs.yml` with paths, docstring_style, show_source, show_root_heading, members_order options
- [x] 1.2 Add `docs/api/reference.md` and `docs/cli.md` to nav in `mkdocs.yml`
- [x] 1.3 Create `docs/guides/usage.md` stub to fix broken nav reference
- [x] 1.4 Remove or fix offline plugin reference if causing build errors

## 2. Fill Docstring Gaps

- [x] 2.1 Add Args block to `Portfolio.__init__` in `src/tiportfolio/portfolio.py` (name, algos, children)
- [x] 2.2 Add Args block to `Backtest.__init__` in `src/tiportfolio/backtest.py` (portfolio, data, config)
- [x] 2.3 Add Returns blocks to `BacktestResult.summary()`, `full_summary()`, `plot()` in `src/tiportfolio/result.py`
- [x] 2.4 Add Args/Raises block to `validate_data` in `src/tiportfolio/data.py`

## 3. Create Auto-Generated Reference Page

- [x] 3.1 Create `docs/api/reference.md` with ::: directives organized by category: Core (Portfolio, Backtest, run, TiConfig), Data (fetch_data, validate_data), Signals (Signal.*), Selection (Select.*), Weighting (Weigh.*), Actions (Action.*), Results (BacktestResult)

## 4. Verification

- [x] 4.1 Run `mkdocs build` and confirm no errors or warnings about missing files
- [x] 4.2 Run `mkdocs serve` briefly to verify reference page renders correctly
- [x] 4.3 Run full test suite to confirm docstring changes didn't break anything
