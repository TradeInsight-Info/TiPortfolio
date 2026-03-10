"""Backtest loop: run logic, rebalance decisions, and result types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from tiportfolio.allocation import AllocationStrategy
from tiportfolio.calendar import get_rebalance_dates
from tiportfolio.metrics import compute_metrics


@dataclass
class RebalanceDecision:
    """Record of a single rebalance: date, target weights, trades, fees, and prices (for quantity)."""

    date: pd.Timestamp
    equity_before: float
    equity_after: float
    target_weights: dict[str, float]
    trades_dollars: dict[str, float]
    fee_paid: float
    prices_at_rebalance: dict[str, float] = field(default_factory=dict)


@dataclass
class BacktestResult:
    """Result of a backtest run."""

    equity_curve: pd.Series
    metrics: dict[str, float]
    rebalance_decisions: list[RebalanceDecision] = field(default_factory=list)
    asset_curves: pd.DataFrame | None = None
    total_fee: float = 0.0
    _cached_benchmark: pd.Series | None = field(default=None, init=False, repr=False)

    def summary(self) -> str:
        """Human-readable summary table."""
        m = self.metrics
        final_value = (
            self.equity_curve.iloc[-1] if not self.equity_curve.empty else float("nan")
        )
        lines = [
            "Backtest Summary",
            "----------------",
            f"Sharpe Ratio:        {m.get('sharpe_ratio', float('nan')):.4f}",
            f"Sortino Ratio:       {m.get('sortino_ratio', float('nan')):.4f}",
            f"MAR Ratio:           {m.get('mar_ratio', float('nan')):.4f}",
            f"CAGR:                {m.get('cagr', float('nan')):.2%}",
            f"Max Drawdown:        {m.get('max_drawdown', float('nan')):.2%}",
            f"Kelly Leverage:      {m.get('kelly_leverage', float('nan')):.4f}",
            f"Mean Excess Return:  {m.get('mean_excess_return', float('nan')):.4f}",
            f"Final Value:         {final_value:,.2f}",
            f"Total Fee:           {self.total_fee:,.2f}",
            f"Rebalances:          {len(self.rebalance_decisions)}",
        ]
        return "\n".join(lines)

    def plot_portfolio(self, *, mark_rebalances: bool = True):
        """Interactive chart (Plotly) of portfolio value.

        Args:
            mark_rebalances: Whether to show buy/sell markers at rebalance dates.

        Returns:
            Plotly Figure object.
        """
        try:
            import plotly.graph_objects as go
        except ImportError:
            raise ImportError(
                "Plotly is required for interactive charts. Install with: uv add --dev plotly"
            ) from None

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=self.equity_curve.index,
                y=self.equity_curve.values,
                name="Total",
                mode="lines",
                line=dict(width=2),
                hovertemplate="Date: %{x|%Y-%m-%d}<br>Value: %{y:,.2f}<extra></extra>",
            )
        )
        if self.asset_curves is not None and not self.asset_curves.empty:
            total_aligned = self.equity_curve.reindex(self.asset_curves.index).fillna(0)
            for col in self.asset_curves.columns:
                pct = self.asset_curves[col] / total_aligned * 100
                pct = pct.replace([np.inf, -np.inf], 0).fillna(0)
                fig.add_trace(
                    go.Scatter(
                        x=self.asset_curves.index,
                        y=self.asset_curves[col].values,
                        name=col,
                        mode="lines",
                        line=dict(width=1),
                        opacity=0.8,
                        customdata=pct.values,
                        hovertemplate=f"Date: %{{x|%Y-%m-%d}}<br>{col}: %{{y:,.2f}} (%{{customdata:.1f}}% of portfolio)<extra></extra>",
                    )
                )
            if mark_rebalances and self.rebalance_decisions:
                for col in self.asset_curves.columns:
                    buy_dates, buy_values, buy_text = [], [], []
                    sell_dates, sell_values, sell_text = [], [], []
                    for d in self.rebalance_decisions:
                        if (
                            d.date not in self.asset_curves.index
                            or col not in d.trades_dollars
                        ):
                            continue
                        trade = d.trades_dollars[col]
                        if trade == 0:
                            continue
                        price = d.prices_at_rebalance.get(col)
                        qty = (trade / price) if price and price != 0 else None
                        date_str = pd.Timestamp(d.date).strftime("%Y-%m-%d")
                        y = self.asset_curves.loc[d.date, col]
                        if trade > 0:
                            buy_dates.append(d.date)
                            buy_values.append(y)
                            price_str = (
                                f"Price: {price:,.2f}"
                                if price is not None
                                else "Price: -"
                            )
                            qty_str = f"<br>Qty: {qty:,.4f}" if qty is not None else ""
                            buy_text.append(
                                f"{col} Buy<br>Date: {date_str}<br>{price_str}{qty_str}"
                            )
                        else:
                            sell_dates.append(d.date)
                            sell_values.append(y)
                            price_str = (
                                f"Price: {price:,.2f}"
                                if price is not None
                                else "Price: -"
                            )
                            qty_str = f"<br>Qty: {qty:,.4f}" if qty is not None else ""
                            sell_text.append(
                                f"{col} Sell<br>Date: {date_str}<br>{price_str}{qty_str}"
                            )
                    if buy_dates:
                        fig.add_trace(
                            go.Scatter(
                                x=buy_dates,
                                y=buy_values,
                                name=f"{col} Buy",
                                mode="markers",
                                marker=dict(
                                    symbol="triangle-up",
                                    size=10,
                                    color="green",
                                    line=dict(width=1.5, color="green"),
                                ),
                                hovertext=buy_text,
                                hoverinfo="text",
                                legendgroup=col,
                                showlegend=False,
                            )
                        )
                    if sell_dates:
                        fig.add_trace(
                            go.Scatter(
                                x=sell_dates,
                                y=sell_values,
                                name=f"{col} Sell",
                                mode="markers",
                                marker=dict(
                                    symbol="triangle-down", size=10, color="red"
                                ),
                                hovertext=sell_text,
                                hoverinfo="text",
                                legendgroup=col,
                                showlegend=False,
                            )
                        )
        fig.update_layout(
            title="Portfolio value: total and by asset",
            xaxis_title="Date",
            yaxis_title="Value",
            hovermode="closest",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            margin=dict(t=80),
        )
        return fig

    def book_composition_table(self, universe: list[str]) -> pd.DataFrame:
        """Return a DataFrame showing Long/Short/Out for each symbol at each rebalance.

        Args:
            universe: Ordered list of symbols to include as columns.

        Returns:
            DataFrame with rebalance dates as index and symbols as columns,
            values are "Long", "Short", or "-".

        Raises:
            ValueError: If there are no rebalance decisions.
        """
        if not self.rebalance_decisions:
            raise ValueError("No rebalance decisions available")

        rows = []
        for d in self.rebalance_decisions:
            row: dict[str, object] = {"date": d.date.date()}
            for s in universe:
                w = d.target_weights.get(s, 0.0)
                if w > 0.01:
                    row[s] = "Long"
                elif w < -0.01:
                    row[s] = "Short"
                else:
                    row[s] = "-"
            rows.append(row)

        return pd.DataFrame(rows).set_index("date")

    def plot_rolling_book_composition(self, universe: list[str]):
        """Visualize long/short book composition over rebalance dates.

        Reads directly from rebalance_decisions.target_weights. Each cell is
        coloured green (Long), red (Short), or grey (Out) based on the signed
        weight at that rebalance.

        Args:
            universe: Ordered list of symbols to display as columns.

        Returns:
            Plotly Figure object showing the heatmap.

        Raises:
            ValueError: If there are no rebalance decisions.
        """
        if not self.rebalance_decisions:
            raise ValueError("No rebalance decisions available")

        try:
            import plotly.graph_objects as go
        except ImportError:
            raise ImportError(
                "Plotly is required for interactive charts. Install with: uv add --dev plotly"
            ) from None

        encode = {"Long": 1, "Short": -1, "-": 0}
        rows = []
        dates = []
        for d in self.rebalance_decisions:
            dates.append(str(d.date.date()))
            row = []
            for s in universe:
                w = d.target_weights.get(s, 0.0)
                if w > 0.01:
                    row.append(encode["Long"])
                elif w < -0.01:
                    row.append(encode["Short"])
                else:
                    row.append(encode["-"])
            rows.append(row)

        fig = go.Figure(
            go.Heatmap(
                z=rows,
                x=universe,
                y=dates,
                colorscale=[[0, "#EF553B"], [0.5, "#EEEEEE"], [1, "#00CC96"]],
                zmin=-1,
                zmax=1,
                colorbar=dict(tickvals=[-1, 0, 1], ticktext=["Short", "Out", "Long"]),
                hoverongaps=False,
            )
        )
        fig.update_layout(
            title="Rolling Book Composition (Long=green, Short=red, Out=grey)",
            xaxis_title="Stock",
            yaxis_title="Rebalance Date",
            height=max(300, 30 * len(dates) + 80),
        )
        return fig

    def plot_portfolio_beta(
        self,
        benchmark_symbol: str = "SPY",
        benchmark_prices: pd.DataFrame | None = None,
        lookback_days: int = 60,
    ):
        """Visualize portfolio beta over time.

        Args:
            benchmark_symbol: Symbol to use as benchmark (default "SPY"). Ignored if benchmark_prices is provided.
            benchmark_prices: DataFrame with benchmark close prices (date index, symbol columns). If None, fetches from YFinance.
            lookback_days: Rolling window for beta calculation.

        Returns:
            Plotly Figure showing rolling portfolio beta over time.

        Examples:
            >>> # Auto-fetch SPY from YFinance
            >>> fig = result.plot_portfolio_beta(lookback_days=60)
            >>> fig.show()
            >>>
            >>> # Use custom benchmark
            >>> benchmark_df = pd.DataFrame({"QQQ": prices}, index=dates)
            >>> fig = result.plot_portfolio_beta(benchmark_symbol="QQQ", benchmark_prices=benchmark_df)
        """
        if self.asset_curves is None or self.asset_curves.empty:
            raise ValueError("asset_curves is not available")

        # Use provided benchmark_prices or fetch/cache
        if benchmark_prices is None or benchmark_prices.empty:
            if self._cached_benchmark is None:
                from tiportfolio.helpers.data import YFinance

                yf = YFinance()
                start_date = self.asset_curves.index[0]
                end_date = self.asset_curves.index[-1]
                benchmark_data = yf.query([benchmark_symbol], start_date, end_date)
                if benchmark_data.empty:
                    raise ValueError(
                        f"Could not fetch benchmark data for {benchmark_symbol}"
                    )
                # Set date index from the DATE column
                if "date" in benchmark_data.columns:
                    benchmark_data = benchmark_data.set_index("date")
                elif "Date" in benchmark_data.columns:
                    benchmark_data = benchmark_data.set_index("Date")
                # Ensure index is DatetimeIndex (YFinance returns RangeIndex by default)
                # This explicit conversion is required for proper index alignment in reindex() operation
                if not isinstance(benchmark_data.index, pd.DatetimeIndex):
                    benchmark_data.index = pd.to_datetime(benchmark_data.index)
                # Use close column
                if "close" in benchmark_data.columns:
                    self._cached_benchmark = benchmark_data["close"]
                elif "Close" in benchmark_data.columns:
                    self._cached_benchmark = benchmark_data["Close"]
                else:
                    self._cached_benchmark = benchmark_data.iloc[:, 0]
            benchmark_prices = self._cached_benchmark.to_frame()

        try:
            import plotly.graph_objects as go
        except ImportError:
            raise ImportError(
                "Plotly is required for interactive charts. Install with: uv add --dev plotly"
            ) from None

        # Normalize indices to tz-naive for alignment
        asset_curves = self.asset_curves.copy()
        benchmark_prices = benchmark_prices.copy()

        # Convert to tz-naive midnight dates for alignment.
        # Use tz_localize(None) to strip tz, then normalize() to zero out any
        # time-of-day offset (e.g. Alpaca returns 05:00:00 UTC for market open).
        try:
            if asset_curves.index.tz is not None:
                asset_curves.index = asset_curves.index.tz_localize(None).normalize()
        except TypeError:
            pass  # Already tz-naive

        try:
            if benchmark_prices.index.tz is not None:
                benchmark_prices.index = benchmark_prices.index.tz_localize(None).normalize()
        except TypeError:
            pass  # Already tz-naive

        # Also normalize tz-naive indices that may carry a time component
        asset_curves.index = asset_curves.index.normalize()
        benchmark_prices.index = benchmark_prices.index.normalize()

        # Find common dates between asset_curves and benchmark_prices
        # Use intersection instead of reindex to handle potential date mismatches
        common_dates = asset_curves.index.intersection(benchmark_prices.index)

        if len(common_dates) < lookback_days + 1:
            raise ValueError(
                f"Not enough overlapping dates. Need at least {lookback_days + 1}, got {len(common_dates)}"
            )

        # Align both to common dates
        asset_aligned = asset_curves.loc[common_dates]
        benchmark_aligned = benchmark_prices.loc[common_dates]

        portfolio_returns = asset_aligned.pct_change().dropna()
        benchmark_symbol = benchmark_prices.columns[0]
        benchmark_returns = benchmark_aligned[benchmark_symbol].pct_change().dropna()

        common_returns_idx = portfolio_returns.index.intersection(
            benchmark_returns.index
        )
        portfolio_returns = portfolio_returns.loc[common_returns_idx]
        benchmark_returns = benchmark_returns.loc[common_returns_idx]

        betas = []
        dates = []
        for i in range(lookback_days, len(common_returns_idx)):
            window_pr = portfolio_returns.iloc[i - lookback_days : i]
            window_br = benchmark_returns.iloc[i - lookback_days : i]

            if len(window_br) < lookback_days:
                betas.append(np.nan)
                dates.append(common_returns_idx[i])
                continue

            # Portfolio returns = sum of asset returns (unweighted)
            portfolio_ret = window_pr.sum(axis=1)
            # Covariance between portfolio returns and benchmark returns
            cov = portfolio_ret.cov(window_br)
            var_bench = window_br.var()
            if var_bench == 0 or pd.isna(cov):
                betas.append(np.nan)
            else:
                portfolio_beta = cov / var_bench
                betas.append(portfolio_beta)
            dates.append(common_returns_idx[i])

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=betas,
                mode="lines",
                name="Portfolio Beta",
                line=dict(width=2),
                hovertemplate="Date: %{x|%Y-%m-%d}<br>Beta: %{y:.4f}<extra></extra>",
            )
        )
        fig.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="β=1")
        fig.add_hline(y=0.0, line_dash="dash", line_color="gray", annotation_text="β=0")
        fig.update_layout(
            title=f"Rolling Portfolio Beta (lookback={lookback_days} days)",
            xaxis_title="Date",
            yaxis_title="Beta",
            hovermode="x unified",
        )
        return fig


def run_backtest(
    prices_df: pd.DataFrame,
    allocation: AllocationStrategy,
    schedule_spec: str,
    fee_per_share: float,
    start: str | pd.Timestamp | None,
    end: str | pd.Timestamp | None,
    initial_value: float = 10000.0,
    rebalance_dates: pd.DatetimeIndex | None = None,
    risk_free_rate: float = 0.0,
    signal_delay: int = 1,
) -> BacktestResult:
    """Core backtest: prices_df has date index and one column per symbol.

    allocation provides symbols and target weights via get_symbols/get_target_weights.
    If rebalance_dates is provided, use those instead of calculating from schedule_spec.
    """
    symbols = allocation.get_symbols()
    if start is not None:
        start = pd.Timestamp(start)
        if hasattr(prices_df.index, "tz") and prices_df.index.tz is not None:
            start = start.tz_localize(prices_df.index.tz) if start.tz is None else start
        prices_df = prices_df.loc[prices_df.index >= start]
    if end is not None:
        end = pd.Timestamp(end)
        if hasattr(prices_df.index, "tz") and prices_df.index.tz is not None:
            end = end.tz_localize(prices_df.index.tz) if end.tz is None else end
        prices_df = prices_df.loc[prices_df.index <= end]
    if prices_df.empty:
        return BacktestResult(
            equity_curve=pd.Series(dtype=float),
            metrics=compute_metrics(
                pd.Series(dtype=float), risk_free_rate=risk_free_rate
            ),
        )

    trading_dates = prices_df.index
    if rebalance_dates is not None:
        rebalance_set = set(rebalance_dates)
    else:
        # signal_delay is intentionally NOT forwarded here for calendar schedules.
        # Calendar rebalance dates (month_end, weekly_monday, etc.) are fixed by the
        # schedule and do not shift with signal_delay. Only prices_history slicing
        # (below, in the main loop) respects signal_delay for calendar schedules.
        rebalance_dates = get_rebalance_dates(
            trading_dates, schedule_spec, start=start, end=end
        )
        rebalance_set = set(rebalance_dates)

    first_date = trading_dates[0]
    first_prices = prices_df.loc[first_date]
    initial_equity = float(initial_value)
    weights0 = allocation.get_target_weights(
        first_date,
        initial_equity,
        {},
        first_prices,
        prices_history=prices_df.loc[:first_date],
    )
    positions_dollars: dict[str, float] = {}
    for sym in symbols:
        positions_dollars[sym] = initial_equity * weights0.get(sym, 0.0)
    equity_curve_list: list[tuple[pd.Timestamp, float]] = []
    asset_curve_rows: list[tuple[pd.Timestamp, dict[str, float]]] = []
    decisions: list[RebalanceDecision] = []
    last_rebalance_date: pd.Timestamp | None = None

    for i, date in enumerate(trading_dates):
        row = prices_df.loc[date]
        if i == 0:
            total_equity = initial_equity
        else:
            prev_date = trading_dates[i - 1]
            prev_row = prices_df.loc[prev_date]
            for s in symbols:
                if prev_row[s] != 0 and not pd.isna(prev_row[s]):
                    ret = (row[s] - prev_row[s]) / prev_row[s]
                    positions_dollars[s] = positions_dollars[s] * (1 + ret)
            total_equity = sum(positions_dollars[s] for s in symbols)

            if date in rebalance_set:
                equity_before = total_equity
                # Compute signal_date: the date when the signal was generated
                # For signal_delay=1, if we execute on day T+1, signal was on day T
                # Clamp to first trading date to handle edge case at start
                signal_idx = max(0, i - signal_delay)
                signal_date = trading_dates[signal_idx]
                # prices_history ends at signal_date (not execution date) to avoid look-ahead bias
                prices_history = prices_df.loc[:signal_date]
                weights = allocation.get_target_weights(
                    date,
                    total_equity,
                    positions_dollars,
                    row,  # prices_row remains execution day's close prices
                    prices_history=prices_history,
                    signal_date=signal_date,
                )
                target_dollars = {
                    s: total_equity * weights.get(s, 0.0) for s in symbols
                }
                trades = {s: target_dollars[s] - positions_dollars[s] for s in symbols}
                fee_paid = 0.0
                for s in symbols:
                    price = float(row[s]) if row[s] and not pd.isna(row[s]) else 0.0
                    if price > 0:
                        trade_qty = trades[s] / price
                        fee_paid += abs(trade_qty) * fee_per_share
                for s in symbols:
                    positions_dollars[s] = target_dollars[s]
                total_equity = sum(positions_dollars[s] for s in symbols) - fee_paid
                last_rebalance_date = date
                if len(symbols) > 1:
                    decisions.append(
                        RebalanceDecision(
                            date=date,
                            equity_before=equity_before,
                            equity_after=total_equity,
                            target_weights=dict(weights),
                            trades_dollars=dict(trades),
                            fee_paid=fee_paid,
                            prices_at_rebalance={s: float(row[s]) for s in symbols},
                        )
                    )

        equity_curve_list.append((date, total_equity))
        asset_curve_rows.append((date, dict(positions_dollars)))

    equity_curve = pd.Series(
        {d: v for d, v in equity_curve_list},
        name="equity",
    ).sort_index()
    asset_curves = None
    if asset_curve_rows:
        dates_index = [d for d, _ in asset_curve_rows]
        asset_curves = pd.DataFrame(
            [v for _, v in asset_curve_rows],
            index=dates_index,
        ).sort_index()
        asset_curves.index.name = "date"
    metrics = compute_metrics(equity_curve, risk_free_rate=risk_free_rate)
    total_fee = sum(d.fee_paid for d in decisions)
    return BacktestResult(
        equity_curve=equity_curve,
        metrics=metrics,
        rebalance_decisions=decisions,
        asset_curves=asset_curves,
        total_fee=total_fee,
    )
