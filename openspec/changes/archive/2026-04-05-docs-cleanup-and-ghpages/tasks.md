> For agentic workers: REQUIRED: Use `subagent-driven-development` (if subagents available) or superpowers:executing-plans to implement these tasks. Steps use checkbox (- [x]) syntax for tracking.

## 1. Critical Doc Fixes

- [x] 1.1 Fix `docs/index.md`: replace `ti.run_backtest()` with `ti.run()`, remove `fee_per_share` from Backtest constructor, fix trade records table to match actual columns (date, portfolio, ticker, qty_before, qty_after, delta, price, fee, equity_before, equity_after), fix summary output to match actual keys (sharpe, calmar, sortino, max_drawdown, cagr, risk_free_rate, total_return, kelly, final_value, total_fee, rebalance_count, leverage), mention `leverage` parameter
- [x] 1.2 Fix `docs/api/index.md`: add `leverage` param to `run()` signature, fix `next_trading_day` → `closest_trading_day` everywhere, fix summary metric table keys, fix `plot()` default to `interactive=False`, remove `interactive` from `plot_histogram()`/`plot_security_weights()`, add missing signals (Weekly, Yearly, Once, EveryNPeriods, Indicator), add `csv` param to `fetch_data`, fix `result.trades` to note it's on `_SingleResult`/`result[0]`, add CLI mention
- [x] 1.3 Fix `docs/api/structure.md`: remove `branching.py` reference, replace `run_backtest()` with `run()`, remove `Context.selected_child`, fix `BacktestResult.trades` description, fix `ti.algo.*` to `ti.Signal.*` etc.

## 2. Minor Doc Fixes

- [x] 2.1 Fix `docs/about.md`: remove or fix broken links to `dimensions/` directory
- [x] 2.2 Fix `docs/guides/fix-time-rebalance.md`: replace `next_trading_day` with `closest_trading_day`
- [x] 2.3 Fix `docs/guides/comparing-results.md`: change `target_hv=60` to `target_hv=0.60`
- [x] 2.4 Fix `docs/guides/allocation-strategies.md`: fix "Voaltility" → "Volatility" typo

## 3. GitHub Pages Workflow

- [x] 3.1 Create `.github/workflows/docs.yml` — on push to master, checkout, setup Python 3.12 + uv, uv sync, mkdocs gh-deploy --force

## 4. Verification

- [x] 4.1 Run `mkdocs build` and confirm no new warnings
- [x] 4.2 Run full test suite to confirm no regressions
