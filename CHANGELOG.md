# Changelog

All notable changes to TiPortfolio are recorded here, derived from completed openspec changes.

---

## [Unreleased]

See [PLANS.md](PLANS.md) for upcoming work.

---

## 2026-04-07

### Added
- **backtest-skill**: Claude Code marketplace skill that maps natural-language strategy descriptions to `uvx tiportfolio` CLI commands and runs backtests. Published as a Claude Code plugin.

---

## 2026-04-06

### Added
- **run-aip**: `ti.run_aip()` function for simulating AIP (Automatic Investment Plan / dollar-cost averaging) — injects a fixed monthly cash contribution on the last trading day of each month and runs the full backtest engine. Returns `BacktestResult` with extra `total_contributions` / `contribution_count` metrics.
- **cli-aip**: `--aip` flag on all CLI subcommands so users can simulate dollar-cost averaging without writing Python code.

---

## 2026-04-05

### Added
- **docs-cleanup-and-ghpages**: Fixed 23 documentation inconsistencies (wrong function names, parameter names, missing features), added GitHub Actions workflow for automatic GitHub Pages deployment.
- **mkdocs-api-docs**: Wired `mkdocstrings[python]` into `mkdocs.yml` so API reference pages auto-generate from Google-style docstrings instead of hand-written Markdown.
- **cloudflare-pages-docs**: Alternative static-site deployment via Cloudflare Pages (free tier, no paid GitHub plan required).

---

## 2026-04-04

### Added
- **build-cli**: Full `tiportfolio` CLI with subcommands (`monthly`, `quarterly`, `weekly`, `yearly`, `every`, `once`), `--select`, `--ratio`, `--leverage`, `--plot`, `--full`, data flags (`--tickers`, `--start`, `--end`, `--source`, `--csv`). Entry point registered in `pyproject.toml`.
- **add-leverage-parameter**: `--leverage` flag accepting a single float or comma-separated list for multi-leverage comparison in a single run.

---

## 2026-04-03

### Added
- **pypi-packaging**: `pyproject.toml` configured for PyPI distribution, `uv publish` workflow documented.
- **github-actions-pypi-publish**: GitHub Actions CI/CD workflow for automated PyPI publishing on tagged releases.

---

## 2026-04-02

### Added
- **signal-indicator**: Non-calendar `Signal.Indicator` that fires based on a user-supplied indicator function rather than calendar dates.
- **interactive-portfolio-chart**: `result.plot()` upgraded to interactive Plotly chart showing equity curve with trade entry/exit annotations.

### Fixed
- **fix-example20-date-range**: Example 20 (`20_fetch_and_hold.py`) date range corrected so both QQQ and ALLW use the proper start date.
- **demo-notebooks-simplify**: Notebooks updated to the new simplified `Portfolio + Algo Stack` API.

---

## 2026-04-01

### Changed
- **chunk-5-2-update-for-summary**: `summary()` revised to return 11 metrics in a consistent, meaningful order; `full_summary()` extended with additional analytics.

---

## 2026-03-31

### Added
- **chunk-5-results-charting**: Basic result charting layer — equity curve, summary metrics table, `result.plot()` entry point.
- **csv-offline-examples**: Examples and e2e tests now use local CSV files in `tests/data/` for reproducible, offline testing.
- **more-examples**: 9 example scripts covering Chunk 1–4 features (advanced weighting, branching, short strategies).

### Fixed
- **chunk-5-1-fixes**: Fixed `summary()` to return full metrics set (total_return, CAGR, max_drawdown, Sharpe, Sortino, Calmar, etc.).

---

## 2026-03-30

### Added
- **chunk-4-advanced-weighting**: `Weigh.ERC` (equal risk contribution), `Weigh.HV` (historical volatility), and ratio-based weighting.
- **chunk-3-trees-shorts**: Parent-child portfolio engine enabling nested portfolio trees and short-selling strategies.
- **chunk-2-algos-branching**: Full algo catalogue — `Select.Momentum`, `Select.All`; quarterly, weekly, yearly, `EveryN`, `Once` signals; explicit ratio weighting.
- **chunk-2-1-signal-flexible-scheduling**: `Signal.Schedule` extended to support `"start"` (month-start), integer day-of-month, and `"end"` (month-end) modes.

---

## 2026-03-29

### Added
- **chunk-1-foundation**: Core backtest engine — `Portfolio`, `Backtest`, `run()`, `BacktestResult`; monthly equal-weight rebalancing with `Signal.Monthly` + `Select.All` + `Weigh.Equal`; `result.summary()` and `result.plot()`.
- **chunk-1-examples**: First set of runnable example scripts demonstrating the new API.
- **chunk-1-cleanup-and-buy-hold**: `Select.BuyAndHold` added; minor cleanup from Chunk 1 review feedback.
