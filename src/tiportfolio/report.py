"""Report: summary table, rebalance decisions table, optional chart."""

from __future__ import annotations

import numpy as np
import pandas as pd

from tiportfolio.backtest import BacktestResult


def summary_table(result: BacktestResult) -> pd.DataFrame:
    """Return metrics as a one-row DataFrame."""
    return pd.DataFrame([result.metrics])


# Metrics used in compare_strategies; higher is better except max_drawdown (lower is better)
_COMPARE_METRICS = ("sharpe_ratio", "cagr", "max_drawdown", "mar_ratio", "final_value")


def compare_strategies(
    result_a: BacktestResult,
    result_b: BacktestResult,
    *,
    name_a: str = "Strategy A",
    name_b: str = "Strategy B",
) -> pd.DataFrame:
    """Compare two backtest results side-by-side.

    Returns a DataFrame with one row per metric (sharpe_ratio, cagr, max_drawdown, mar_ratio),
    columns for each strategy's value, and a 'better' column (A, B, or tie).
    Higher is better for Sharpe, CAGR, MAR; lower is better for max_drawdown.
    """
    rows = []
    for key in _COMPARE_METRICS:
        if key == "final_value":
            # Get final value from equity curve
            va = result_a.equity_curve.iloc[-1] if not result_a.equity_curve.empty else float("nan")
            vb = result_b.equity_curve.iloc[-1] if not result_b.equity_curve.empty else float("nan")
            better = "A" if va > vb else ("B" if vb > va else "tie")
        else:
            va = result_a.metrics.get(key, float("nan"))
            vb = result_b.metrics.get(key, float("nan"))
            if key == "max_drawdown":
                better = "A" if va < vb else ("B" if vb < va else "tie")
            else:
                better = "A" if va > vb else ("B" if vb > va else "tie")
        rows.append({name_a: va, name_b: vb, "better": better})
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


def plot_equity_curve(
    result: BacktestResult,
    *,
    ax=None,
    mark_rebalances: bool = True,
):
    """Plot equity curve; optionally mark rebalance dates. Returns matplotlib axes."""
    import matplotlib.pyplot as plt
    if ax is None:
        _, ax = plt.subplots()
    result.equity_curve.plot(ax=ax, label="Equity")
    if mark_rebalances and result.rebalance_decisions:
        dates = [d.date for d in result.rebalance_decisions]
        values = [
            result.equity_curve.loc[d.date] if d.date in result.equity_curve.index else float("nan")
            for d in result.rebalance_decisions
        ]
        ax.scatter(dates, values, color="red", marker="v", zorder=5, label="Rebalance")
    ax.set_title("Portfolio equity")
    ax.set_ylabel("Equity")
    ax.legend()
    ax.grid(True, alpha=0.3)
    return ax


def plot_portfolio_with_assets(
    result: BacktestResult,
    *,
    ax=None,
    mark_rebalances: bool = True,
):
    """Plot overall portfolio value and each asset's value over time. Returns matplotlib axes."""
    import matplotlib.pyplot as plt
    if ax is None:
        _, ax = plt.subplots()
    result.equity_curve.plot(ax=ax, label="Total", linewidth=2)
    if result.asset_curves is not None and not result.asset_curves.empty:
        for col in result.asset_curves.columns:
            result.asset_curves[col].plot(ax=ax, label=col, alpha=0.8)
    if mark_rebalances and result.rebalance_decisions and result.asset_curves is not None:
        buy_dates, buy_values = [], []
        sell_dates, sell_values = [], []
        for d in result.rebalance_decisions:
            if d.date not in result.asset_curves.index:
                continue
            for symbol, trade in d.trades_dollars.items():
                if symbol not in result.asset_curves.columns:
                    continue
                y = result.asset_curves.loc[d.date, symbol]
                if trade > 0:
                    buy_dates.append(d.date)
                    buy_values.append(y)
                elif trade < 0:
                    sell_dates.append(d.date)
                    sell_values.append(y)
        if buy_dates:
            ax.scatter(
                buy_dates, buy_values,
                facecolors="none", edgecolors="green", marker="^",
                s=60, zorder=5, label="Buy", linewidths=1.5,
            )
        if sell_dates:
            ax.scatter(
                sell_dates, sell_values,
                c="red", marker="v", s=60, zorder=5, label="Sell",
            )
    ax.set_title("Portfolio value: total and by asset")
    ax.set_ylabel("Value")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    return ax


def plot_portfolio_with_assets_interactive(
    result: BacktestResult,
    *,
    mark_rebalances: bool = True,
):
    """Interactive chart (Plotly). Total line: hover shows date and value only.
    Asset lines: hover shows date and value; buy/sell markers on asset lines show price and quantity.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        raise ImportError(
            "Plotly is required for interactive charts. Install with: uv add --dev plotly"
        ) from None

    fig = go.Figure()
    # Total line: hover = date + value only (no buy/sell)
    fig.add_trace(
        go.Scatter(
            x=result.equity_curve.index,
            y=result.equity_curve.values,
            name="Total",
            mode="lines",
            line=dict(width=2),
            hovertemplate="Date: %{x|%Y-%m-%d}<br>Value: %{y:,.2f}<extra></extra>",
        )
    )
    # Per-asset lines and their buy/sell markers (markers only when hovering asset line / marker)
    if result.asset_curves is not None and not result.asset_curves.empty:
        total_aligned = result.equity_curve.reindex(result.asset_curves.index).fillna(0)
        for col in result.asset_curves.columns:
            pct = result.asset_curves[col] / total_aligned * 100
            pct = pct.replace([np.inf, -np.inf], 0).fillna(0)
            fig.add_trace(
                go.Scatter(
                    x=result.asset_curves.index,
                    y=result.asset_curves[col].values,
                    name=col,
                    mode="lines",
                    line=dict(width=1),
                    opacity=0.8,
                    customdata=pct.values,
                    hovertemplate=f"Date: %{{x|%Y-%m-%d}}<br>{col}: %{{y:,.2f}} (%{{customdata:.1f}}% of portfolio)<extra></extra>",
                )
            )
        # Buy/sell markers per asset: only show when hover on that marker (price + quantity)
        if mark_rebalances and result.rebalance_decisions:
            for col in result.asset_curves.columns:
                buy_dates, buy_values, buy_text = [], [], []
                sell_dates, sell_values, sell_text = [], [], []
                for d in result.rebalance_decisions:
                    if d.date not in result.asset_curves.index or col not in d.trades_dollars:
                        continue
                    trade = d.trades_dollars[col]
                    if trade == 0:
                        continue
                    price = d.prices_at_rebalance.get(col)
                    qty = (trade / price) if price and price != 0 else None
                    date_str = pd.Timestamp(d.date).strftime("%Y-%m-%d")
                    y = result.asset_curves.loc[d.date, col]
                    if trade > 0:
                        buy_dates.append(d.date)
                        buy_values.append(y)
                        price_str = f"Price: {price:,.2f}" if price is not None else "Price: -"
                        qty_str = f"<br>Qty: {qty:,.4f}" if qty is not None else ""
                        buy_text.append(f"{col} Buy<br>Date: {date_str}<br>{price_str}{qty_str}")
                    else:
                        sell_dates.append(d.date)
                        sell_values.append(y)
                        price_str = f"Price: {price:,.2f}" if price is not None else "Price: -"
                        qty_str = f"<br>Qty: {qty:,.4f}" if qty is not None else ""
                        sell_text.append(f"{col} Sell<br>Date: {date_str}<br>{price_str}{qty_str}")
                if buy_dates:
                    fig.add_trace(
                        go.Scatter(
                            x=buy_dates, y=buy_values,
                            name=f"{col} Buy",
                            mode="markers",
                            marker=dict(symbol="triangle-up", size=10, color="green", line=dict(width=1.5, color="green")),
                            hovertext=buy_text, hoverinfo="text",
                            legendgroup=col, showlegend=False,
                        )
                    )
                if sell_dates:
                    fig.add_trace(
                        go.Scatter(
                            x=sell_dates, y=sell_values,
                            name=f"{col} Sell",
                            mode="markers",
                            marker=dict(symbol="triangle-down", size=10, color="red"),
                            hovertext=sell_text, hoverinfo="text",
                            legendgroup=col, showlegend=False,
                        )
                    )
    fig.update_layout(
        title="Portfolio value: total and by asset",
        xaxis_title="Date",
        yaxis_title="Value",
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=80),
    )
    return fig


def plot_strategy_comparison_interactive(
    result_a: BacktestResult,
    result_b: BacktestResult,
    *,
    name_a: str = "Strategy A",
    name_b: str = "Strategy B",
):
    """Interactive comparison chart (Plotly) for two strategies."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        raise ImportError(
            "Plotly is required for interactive charts. Install with: uv add --dev plotly"
        ) from None

    fig = go.Figure()
    
    # Strategy A line
    fig.add_trace(
        go.Scatter(
            x=result_a.equity_curve.index,
            y=result_a.equity_curve.values,
            name=name_a,
            mode="lines",
            line=dict(width=2),
            hovertemplate=f"Date: %{{x|%Y-%m-%d}}<br>{name_a}: %{{y:,.2f}}<extra></extra>",
        )
    )
    
    # Strategy B line
    fig.add_trace(
        go.Scatter(
            x=result_b.equity_curve.index,
            y=result_b.equity_curve.values,
            name=name_b,
            mode="lines",
            line=dict(width=2),
            hovertemplate=f"Date: %{{x|%Y-%m-%d}}<br>{name_b}: %{{y:,.2f}}<extra></extra>",
        )
    )
    
    fig.update_layout(
        title=f"Equity: {name_a} vs {name_b}",
        xaxis_title="Date",
        yaxis_title="Value",
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=80),
    )
    return fig
