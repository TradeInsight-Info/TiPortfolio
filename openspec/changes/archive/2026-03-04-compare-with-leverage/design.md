## Context

`compare_strategies()` in `report.py` currently compares raw backtest metrics. It has no concept of leverage or borrowing cost. A user running a 1.5× leveraged portfolio needs to see adjusted metrics (larger drawdown, different CAGR, recomputed MAR) to make a meaningful comparison — without having to re-run backtests.

## Goals / Non-Goals

**Goals:**
- Add `leverages` and `yearly_loan_rates` params to both `compare_strategies()` and `plot_strategy_comparison_interactive()` with sensible defaults
- Adjust `max_drawdown`, `cagr`, and `mar_ratio` on the fly before comparison (table)
- Reconstruct leveraged equity curves for visualization (chart)
- Leave `sharpe_ratio` and `sortino_ratio` unchanged in both functions
- Validate list lengths when list inputs are provided
- Decorate column headers and chart legend entries when leverage is applied

**Non-Goals:**
- Modifying `BacktestResult` or `compute_metrics()` — adjustments are purely in the comparison/visualization layer
- Re-running the backtest simulation with leverage
- Adjusting per-asset curves or rebalance decision records

## Decisions

**Leverage math (no initial_value needed)**

All three adjusted metrics are ratio-based and do not require absolute dollar amounts:

| Metric | Formula |
|--------|---------|
| `max_drawdown` | `L × dd` |
| `cagr` | `L × cagr − (L − 1) × r` |
| `mar_ratio` | `leveraged_cagr / leveraged_max_drawdown` |

The CAGR formula assumes constant-leverage rebalancing (standard margin model): the borrowed amount scales with equity each period, so loan interest ≈ `(L−1) × r` per year regardless of the absolute portfolio size. This means no initial_value is needed.

**Sharpe/Sortino unchanged**

Under constant-leverage rebalancing, both excess return and volatility scale by L, so their ratio is preserved. The proposal explicitly requires these to be unchanged, and this is consistent with the standard result from portfolio theory.

**Scalar vs list inputs**

Accept `float | list[float]`. Normalise scalars to `[value] * N` before processing. Validate list length == `len(results)` upfront and raise `ValueError` with a clear message.

**Column header decoration**

When any strategy has leverage ≠ 1.0, append `(L{L}x)` to that strategy's column name in the output DataFrame (e.g., `"A (L1.5x)"`). When loan rate is also non-zero, append `(L{L}x, r{r:.1%})`. This makes it visually clear which columns reflect adjusted metrics.

**Leveraged equity curve reconstruction (chart function)**

The chart plots dollar values, so we must rebuild the equity curve using leveraged daily returns:

```
leveraged_r[t] = L × r[t] − (L−1) × (yearly_loan_rate / 252)
equity_lev[0]  = equity_curve.iloc[0]   # same starting equity
equity_lev[t]  = equity_lev[0] × cumprod(1 + leveraged_r)
```

This preserves the starting equity (the investor's own capital is unchanged; they borrowed extra) and compounds at the leveraged rate. The initial_value is read from `equity_curve.iloc[0]`, so no new parameter is needed.

When L = 1.0 and r = 0.0, the reconstructed curve equals the original exactly — no branch needed.

**MAR when max_drawdown is 0 after leverage**

If `leveraged_max_drawdown` is 0 (implying original drawdown was 0), MAR remains `nan` — same guard as existing logic.

**Shared helpers**

Both functions share:
- `_normalize_leverage_param(value, n)` — scalar-to-list normalisation + length validation
- `_build_display_name(name, L, r)` — produces decorated name or plain name

Each function has its own adjustment helper:
- `_apply_leverage(metrics, L, r)` — table: returns adjusted metrics dict
- `_make_leveraged_equity_curve(equity_curve, L, r)` — chart: returns adjusted `pd.Series`

## Risks / Trade-offs

- [Risk] `leveraged_cagr` can go negative (e.g., 1.5× a -5% CAGR strategy with 8% loan rate) → Mitigation: no special handling needed; negative CAGR is correct and meaningful
- [Risk] `leveraged_max_drawdown` can exceed 1.0 (100%) with high leverage → Mitigation: no clamping; values >100% are technically possible (equity wiped out and more) and should surface as-is
- [Trade-off] Loan interest formula assumes continuous compounding / constant leverage rather than discrete daily interest → acceptable approximation for annual comparison purposes
- [Trade-off] Column decoration changes the DataFrame structure (column names) when leverage is applied — downstream code using hardcoded column names will break → Mitigation: document clearly; the `names` parameter still controls base names
