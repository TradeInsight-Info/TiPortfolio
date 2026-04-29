# Plans

Upcoming features and work items for TiPortfolio, drawn from capability specs in `openspec/specs/`.

---

## In Progress

_Nothing currently in progress._

---

## Planned

### Analytics & Metrics

- **drawdown-analysis** — Add `avg_drawdown`, `avg_drawdown_days`, `avg_up_month`, `avg_down_month`, `win_year_pct`, `win_12m_pct` to `full_summary()`. Spec: `openspec/specs/drawdown-analysis/spec.md`
- **frequency-statistics** — Per-period return statistics (monthly/quarterly/yearly breakdown, win rate, best/worst period). Spec: `openspec/specs/frequency-statistics/spec.md`
- **period-returns** — Structured period-over-period return table accessible via `result.period_returns`. Spec: `openspec/specs/period-returns/spec.md`

### Signals & Strategies

- **vix-signal** — `Signal.VIX` for regime switching between two child portfolios based on VIX level with hysteresis (`high`/`low` thresholds). Spec: `openspec/specs/vix-signal/spec.md`
- **signal-indicator** — `Signal.Indicator` accepting a user-supplied callable to fire on arbitrary conditions. Spec: `openspec/specs/signal-indicator/spec.md`
- **every-n-periods-signal** — `Signal.EveryN` for custom N-period cadence. Spec: `openspec/specs/every-n-periods-signal/spec.md`

### Weighting Strategies

- **beta-neutral-weighting** — `Weigh.BasedOnBeta` iteratively adjusts weights to reach a target portfolio beta (default 0 = beta-neutral) against a benchmark. Spec: `openspec/specs/beta-neutral-weighting/spec.md`

### Data & Infrastructure

- **data-normalization** — Internal `_normalize_ticker_df()` helper: lowercase columns, UTC conversion, sort, drop all-NaN rows. Spec: `openspec/specs/data-normalization/spec.md`
- **daily-carry-costs** — Model daily borrowing/financing costs for leveraged or short positions. Spec: `openspec/specs/daily-carry-costs/spec.md`
- **csv-offline-data** — Extended CSV data source support for fully offline backtesting. Spec: `openspec/specs/csv-offline-data/spec.md`

### Documentation & DX

- **api-reference-autodoc** — Auto-generate API reference pages from docstrings via `mkdocstrings`. Spec: `openspec/specs/api-reference-autodoc/spec.md`
- **docstring-completion** — Audit and complete Google-style docstrings across all public APIs. Spec: `openspec/specs/docstring-completion/spec.md`
- **docs-consistency-fixes** — Fix remaining doc inconsistencies post-refactor. Spec: `openspec/specs/docs-consistency-fixes/spec.md`
- **chart-enhancements** — Enhanced chart styling, benchmark overlay, annotation improvements. Spec: `openspec/specs/chart-enhancements/spec.md`

### Notebooks & Examples

- **vix-regime-notebook** — Jupyter notebook demonstrating VIX regime-switching strategies. Spec: `openspec/specs/vix-regime-notebook/spec.md`
- **beta-neutral-notebook** — Notebook demonstrating beta-neutral portfolio construction. Spec: `openspec/specs/beta-neutral-notebook/spec.md`
- **dollar-neutral-notebook** — Notebook for dollar-neutral (long-short) strategies. Spec: `openspec/specs/dollar-neutral-notebook/spec.md`
- **volatility-targeting-notebook** — Notebook for volatility-targeting weighting strategies. Spec: `openspec/specs/volatility-targeting-notebook/spec.md`
- **start-of-month-notebook** — Notebook demonstrating start-of-month rebalancing vs end-of-month. Spec: `openspec/specs/start-of-month-notebook/spec.md`

### Plugins & Integrations

- **backtest-skill** — Claude Code marketplace skill for running backtests via natural language. Spec: `openspec/specs/backtest-skill/spec.md`
- **ci-pypi-publish** — CI pipeline for automated PyPI publishing. Spec: `openspec/specs/ci-pypi-publish/spec.md`
- **ghpages-deployment** — GitHub Actions workflow for docs deployment to GitHub Pages. Spec: `openspec/specs/ghpages-deployment/spec.md`
- **mkdocstrings-config** — MkDocs + mkdocstrings configuration for auto API docs. Spec: `openspec/specs/mkdocstrings-config/spec.md`

---

## Completed

See [CHANGELOG.md](CHANGELOG.md) for all completed work.
