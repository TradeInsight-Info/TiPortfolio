"""Report: summary table, rebalance decisions table, optional chart."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tiportfolio.backtest import BacktestResult


def summary_table(result: BacktestResult) -> pd.DataFrame:
    """Return metrics as a one-row DataFrame."""
    return pd.DataFrame([result.metrics])


def _normalize_leverage_param(value: float | list[float], n: int, param_name: str) -> list[float]:
    """Convert scalar to list of length n, or validate list length equals n."""
    if isinstance(value, (int, float)):
        return [float(value)] * n
    if len(value) != n:
        raise ValueError(
            f"{param_name} must be a float or list of length {n}; got list of length {len(value)}"
        )
    return list(value)


def _build_display_name(name: str, L: float, r: float) -> str:
    """Return decorated strategy name when leverage is applied."""
    if L == 1.0:
        return name
    if r == 0.0:
        return f"{name} (L{L}x)"
    return f"{name} (L{L}x, r{r:.1%})"


def _apply_leverage(metrics: dict, L: float, r: float) -> dict:
    """Return a copy of metrics with max_drawdown, cagr, mar_ratio adjusted for leverage L and loan rate r.

    sharpe_ratio and sortino_ratio are unchanged.
    """
    if L == 1.0 and r == 0.0:
        return metrics
    m = dict(metrics)
    lev_dd = L * m.get("max_drawdown", float("nan"))
    lev_cagr = L * m.get("cagr", float("nan")) - (L - 1) * r
    lev_mar = lev_cagr / lev_dd if lev_dd and lev_dd > 0 else float("nan")
    m["max_drawdown"] = lev_dd
    m["cagr"] = lev_cagr
    m["mar_ratio"] = lev_mar
    return m


def _make_leveraged_equity_curve(equity_curve: pd.Series, L: float, r: float) -> pd.Series:
    """Reconstruct equity curve with leverage L and annual loan rate r applied.

    leveraged_r[t] = L * r_t - (L-1) * r/252
    Starting equity is preserved; subsequent values compound at the leveraged rate.
    """
    if L == 1.0 and r == 0.0:
        return equity_curve
    daily_rf = r / 252
    daily_returns = equity_curve.pct_change()
    leveraged_returns = L * daily_returns - (L - 1) * daily_rf
    leveraged_returns.iloc[0] = 0.0  # preserve starting equity
    return equity_curve.iloc[0] * (1 + leveraged_returns).cumprod()


# Top-5 metrics used in compare_strategies; higher is better except max_drawdown (lower is better)
_COMPARE_METRICS = ("sharpe_ratio", "sortino_ratio", "mar_ratio", "cagr", "max_drawdown")


def compare_strategies(
    *results,
    names=None,
    leverages: float | list[float] = 1.0,
    yearly_loan_rates: float | list[float] = 0.0,
):
    """Compare multiple backtest results side-by-side.

    Args:
        *results: BacktestResult instances to compare
        names: Optional list of names for each strategy. Auto-generated if None.
        leverages: Leverage factor(s). Float applies to all; list must match len(results).
        yearly_loan_rates: Annual borrowing rate(s). Float applies to all; list must match len(results).

    Returns:
        DataFrame with one row per metric, columns for each strategy's value, and a 'better' column with the best strategy name.
        Compares top-5 metrics: sharpe_ratio, sortino_ratio, mar_ratio, cagr, max_drawdown.
        Higher is better for all except max_drawdown (lower is better).
        When leverage != 1.0, column headers are decorated (e.g. "A (L1.5x)") and metrics are adjusted.
    """
    n = len(results)
    if names is None:
        names = [f"Strategy {i+1}" for i in range(n)]
    lev_list = _normalize_leverage_param(leverages, n, "leverages")
    rate_list = _normalize_leverage_param(yearly_loan_rates, n, "yearly_loan_rates")
    display_names = [_build_display_name(name, L, r) for name, L, r in zip(names, lev_list, rate_list)]
    adjusted = [_apply_leverage(result.metrics, L, r) for result, L, r in zip(results, lev_list, rate_list)]

    rows = []
    for key in _COMPARE_METRICS:
        values = [m.get(key, float("nan")) for m in adjusted]
        row = {display_names[i]: v for i, v in enumerate(values)}

        # Determine best strategy; max is better except max_drawdown (lower is better)
        valid_values = [v for v in values if not pd.isna(v)]
        if not valid_values:
            best_name = "N/A"
        else:
            best_val = min(valid_values) if key == "max_drawdown" else max(valid_values)
            best_count = valid_values.count(best_val)
            if best_count > 1:
                best_name = "tie"
            else:
                best_name = display_names[values.index(best_val)]

        row["better"] = best_name
        rows.append(row)

    df = pd.DataFrame(rows, index=list(_COMPARE_METRICS))
    df.index.name = "metric"
    return df


def rebalance_decisions_table(result: BacktestResult) -> pd.DataFrame:
    """Return rebalance decisions as a DataFrame.
    Per-asset columns (symbol first): {s}_price, {s}_qty_before, {s}_trade_qty, {s}_qty_after, {s}_value_after.
    """
    if not result.rebalance_decisions:
        return pd.DataFrame()
    rows = []
    for d in result.rebalance_decisions:
        total_after_before_fee = d.equity_after + d.fee_paid
        row = {
            "date": d.date,
            "equity_before": d.equity_before,
            "equity_after": d.equity_after,
            "fee_paid": d.fee_paid,
        }
        for s in d.trades_dollars:
            trade = d.trades_dollars[s]
            price = d.prices_at_rebalance.get(s) if d.prices_at_rebalance else None
            target_dollars = total_after_before_fee * d.target_weights.get(s, 0)
            position_before_dollars = target_dollars - trade
            trade_qty = (trade / price) if price and price != 0 else None
            qty_before = (position_before_dollars / price) if price and price != 0 else None
            qty_after = (target_dollars / price) if price and price != 0 else None
            row[f"{s}_price"] = price
            row[f"{s}_qty_before"] = qty_before
            row[f"{s}_trade_qty"] = trade_qty
            row[f"{s}_qty_after"] = qty_after
            row[f"{s}_value_after"] = target_dollars
        rows.append(row)
    df = pd.DataFrame(rows)
    # Round numeric columns to max 3 decimals for display
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].round(3)
    return df


def plot_strategy_comparison_interactive(
    *strategies: BacktestResult,
    names: list[str] | None = None,
    leverages: float | list[float] = 1.0,
    yearly_loan_rates: float | list[float] = 0.0,
):
    """Interactive comparison chart (Plotly) for multiple strategies.

    Args:
        *strategies: BacktestResult instances to compare
        names: Optional list of names for each strategy. Auto-generated if None.
        leverages: Leverage factor(s). Float applies to all; list must match len(strategies).
        yearly_loan_rates: Annual borrowing rate(s). Float applies to all; list must match len(strategies).

    When leverage != 1.0, equity curves are reconstructed using leveraged daily returns and
    legend entries are decorated (e.g. "A (L1.5x)").
    """
    if not strategies:
        raise ValueError("At least one strategy is required")

    if names is None:
        names = [f"Strategy {i+1}" for i in range(len(strategies))]
    elif len(names) != len(strategies):
        raise ValueError(f"names must have {len(strategies)} elements, got {len(names)}")

    n = len(strategies)
    lev_list = _normalize_leverage_param(leverages, n, "leverages")
    rate_list = _normalize_leverage_param(yearly_loan_rates, n, "yearly_loan_rates")
    display_names = [_build_display_name(name, L, r) for name, L, r in zip(names, lev_list, rate_list)]

    try:
        import plotly.graph_objects as go
    except ImportError:
        raise ImportError(
            "Plotly is required for interactive charts. Install with: uv add --dev plotly"
        ) from None

    fig = go.Figure()

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    for i, (strategy, display_name) in enumerate(zip(strategies, display_names)):
        L = lev_list[i]
        r = rate_list[i]
        equity = _make_leveraged_equity_curve(strategy.equity_curve, L, r)
        color = colors[i % len(colors)]
        fig.add_trace(
            go.Scatter(
                x=equity.index,
                y=equity.values,
                name=display_name,
                mode="lines",
                line=dict(width=2, color=color),
                hovertemplate=f"Date: %{{x|%Y-%m-%d}}<br>{display_name}: %{{y:,.2f}}<extra></extra>",
            )
        )

    if len(display_names) == 2:
        title = f"Equity: {display_names[0]} vs {display_names[1]}"
    else:
        title = f"Equity: {len(strategies)} Strategies Comparison"

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Value",
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=80),
    )
    return fig
