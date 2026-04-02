from __future__ import annotations

import math
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tiportfolio.config import TiConfig


def _round_values(data: dict[str, Any], decimals: int = 3) -> dict[str, Any]:
    """Round float values to *decimals* places, leaving ints and NaN untouched."""
    out: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, float) and not math.isnan(v):
            out[k] = round(v, decimals)
        else:
            out[k] = v
    return out


class Trades:
    """Wraps a DataFrame of trade records with delegation and sample()."""

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    def __getattr__(self, name: str) -> Any:
        return getattr(self._df, name)

    def __getitem__(self, key: Any) -> Any:
        return self._df[key]

    def __len__(self) -> int:
        return len(self._df)

    def __repr__(self) -> str:
        return repr(self._df)

    def sample(self, n: int = 5) -> pd.DataFrame:
        """Return top-N and bottom-N rebalances by equity return.

        Deduplicates when 2*n >= len(trades).
        """
        df = self._df.copy()
        df["equity_return"] = df["equity_after"].astype(float) - df["equity_before"].astype(float)
        top = df.nlargest(n, "equity_return")
        bottom = df.nsmallest(n, "equity_return")
        combined = pd.concat([top, bottom])
        combined = combined[~combined.index.duplicated()]
        return combined.drop(columns=["equity_return"])


class _SingleResult:
    """Holds results for a single backtest."""

    def __init__(
        self,
        name: str,
        equity_curve: pd.Series,  # type: ignore[type-arg]
        config: TiConfig,
        trade_records: list[dict[str, object]] | None = None,
        weight_history: list[dict[str, object]] | None = None,
        total_fee: float = 0.0,
        rebalance_count: int = 0,
        prices: dict[str, pd.DataFrame] | None = None,
    ) -> None:
        self.name = name
        self.equity_curve = equity_curve
        self._config = config
        self._trade_records = trade_records or []
        self._weight_history = weight_history or []
        self._total_fee = total_fee
        self._rebalance_count = rebalance_count
        self._prices = prices or {}

    @property
    def trades(self) -> Trades:
        """Access trade records as a Trades wrapper."""
        df = pd.DataFrame(self._trade_records) if self._trade_records else pd.DataFrame(
            columns=["date", "portfolio", "ticker", "qty_before", "qty_after",
                     "delta", "price", "fee", "equity_before", "equity_after"]
        )
        return Trades(df)

    def summary(self) -> pd.DataFrame:
        """Return a DataFrame with key performance metrics matching docs/api/index.md."""
        eq = self.equity_curve
        bars_per_year = self._config.bars_per_year
        rf_per_bar = self._config.risk_free_rate / bars_per_year

        total_return = (eq.iloc[-1] / eq.iloc[0]) - 1.0

        # CAGR
        n_bars = len(eq)
        years = n_bars / bars_per_year
        cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1.0 if years > 0 else 0.0

        # Max drawdown
        cummax = eq.cummax()
        drawdown = (eq - cummax) / cummax
        max_dd = drawdown.min()

        # Daily returns and excess
        returns = eq.pct_change().dropna()
        excess = returns - rf_per_bar

        # Annualised Sharpe ratio
        sharpe = (
            float(excess.mean()) / float(excess.std()) * math.sqrt(bars_per_year)
            if float(excess.std()) > 0
            else 0.0
        )

        # Annualised Sortino ratio (downside deviation only)
        downside = excess[excess < 0]
        downside_std = float(downside.std()) if len(downside) > 0 else 0.0
        sortino = (
            float(excess.mean()) / downside_std * math.sqrt(bars_per_year)
            if downside_std > 0
            else 0.0
        )

        # Calmar ratio (CAGR / |max_drawdown|)
        calmar = abs(cagr / max_dd) if max_dd != 0 else 0.0

        # Kelly leverage (mean_excess / var_excess)
        excess_var = float(excess.var())
        kelly = float(excess.mean()) / excess_var if excess_var > 0 else 0.0

        data = {
            "sharpe": sharpe,
            "calmar": calmar,
            "sortino": sortino,
            "max_drawdown": max_dd,
            "cagr": cagr,
            "risk_free_rate": self._config.risk_free_rate,
            "total_return": total_return,
            "kelly": kelly,
            "final_value": float(eq.iloc[-1]),
            "total_fee": self._total_fee,
            "rebalance_count": self._rebalance_count,
        }
        data = _round_values(data)
        return pd.DataFrame(
            {"value": data.values()},
            index=list(data.keys()),
        )

    def full_summary(self) -> pd.DataFrame:
        """Return extended performance metrics. Superset of summary()."""
        base = self.summary()
        data: dict[str, Any] = {k: v for k, v in base["value"].items()}

        data.update(self._period_returns())
        data.update(self._daily_stats())
        data.update(self._monthly_stats())
        data.update(self._yearly_stats())
        data.update(self._drawdown_analysis())

        data = _round_values(data)
        return pd.DataFrame(
            {"value": data.values()},
            index=list(data.keys()),
        )

    # ------------------------------------------------------------------
    # full_summary helper methods
    # ------------------------------------------------------------------

    def _period_returns(self) -> dict[str, Any]:
        """Trailing period returns from the equity curve."""
        eq = self.equity_curve
        last_date = eq.index[-1]
        bars_per_year = self._config.bars_per_year

        def _ret(start_date: pd.Timestamp) -> float:
            """Simple return from start_date to last equity value."""
            idx = eq.index.searchsorted(start_date)
            if idx >= len(eq):
                return float("nan")
            return float(eq.iloc[-1] / eq.iloc[idx] - 1.0)

        def _ann_ret(start_date: pd.Timestamp, years: float) -> float:
            """Annualised return from start_date."""
            idx = eq.index.searchsorted(start_date)
            if idx >= len(eq):
                return float("nan")
            ratio = eq.iloc[-1] / eq.iloc[idx]
            return float(ratio ** (1.0 / years) - 1.0)

        first_date = eq.index[0]
        total_years = len(eq) / bars_per_year

        # Month-to-date: start of current month
        mtd_start = last_date.replace(day=1)
        # Year-to-date: start of current year
        ytd_start = last_date.replace(month=1, day=1)

        # Lookback dates
        m3_start = last_date - pd.DateOffset(months=3)
        m6_start = last_date - pd.DateOffset(months=6)
        y1_start = last_date - pd.DateOffset(years=1)
        y3_start = last_date - pd.DateOffset(years=3)
        y5_start = last_date - pd.DateOffset(years=5)
        y10_start = last_date - pd.DateOffset(years=10)

        return {
            "mtd": _ret(mtd_start),
            "3m": _ret(m3_start),
            "6m": _ret(m6_start),
            "ytd": _ret(ytd_start),
            "1y": _ret(y1_start),
            "3y_ann": _ann_ret(y3_start, 3.0) if y3_start >= first_date else float("nan"),
            "5y_ann": _ann_ret(y5_start, 5.0) if y5_start >= first_date else float("nan"),
            "10y_ann": _ann_ret(y10_start, 10.0) if y10_start >= first_date else float("nan"),
            "incep_ann": float(
                (eq.iloc[-1] / eq.iloc[0]) ** (1.0 / total_years) - 1.0
            ) if total_years > 0 else 0.0,
        }

    def _daily_stats(self) -> dict[str, float]:
        """Daily return statistics."""
        bars_per_year = self._config.bars_per_year
        daily = self.equity_curve.pct_change().dropna()

        return {
            "daily_mean_ann": float(daily.mean() * bars_per_year),
            "daily_vol_ann": float(daily.std() * math.sqrt(bars_per_year)),
            "daily_skew": float(daily.skew()),
            "daily_kurt": float(daily.kurt()),
            "best_day": float(daily.max()),
            "worst_day": float(daily.min()),
        }

    def _monthly_stats(self) -> dict[str, float]:
        """Monthly return statistics."""
        eq = self.equity_curve
        rf = self._config.risk_free_rate
        monthly = eq.resample("ME").last().pct_change().dropna()

        if len(monthly) < 2:
            return {
                "monthly_sharpe": 0.0, "monthly_sortino": 0.0,
                "monthly_mean_ann": 0.0, "monthly_vol_ann": 0.0,
                "monthly_skew": 0.0, "monthly_kurt": 0.0,
                "best_month": float(monthly.max()) if len(monthly) > 0 else 0.0,
                "worst_month": float(monthly.min()) if len(monthly) > 0 else 0.0,
            }

        rf_monthly = rf / 12.0
        excess = monthly - rf_monthly
        std = float(excess.std())
        downside = excess[excess < 0]
        down_std = float(downside.std()) if len(downside) > 0 else 0.0

        return {
            "monthly_sharpe": float(excess.mean()) / std * math.sqrt(12) if std > 0 else 0.0,
            "monthly_sortino": float(excess.mean()) / down_std * math.sqrt(12) if down_std > 0 else 0.0,
            "monthly_mean_ann": float(monthly.mean() * 12),
            "monthly_vol_ann": float(monthly.std() * math.sqrt(12)),
            "monthly_skew": float(monthly.skew()),
            "monthly_kurt": float(monthly.kurt()),
            "best_month": float(monthly.max()),
            "worst_month": float(monthly.min()),
        }

    def _yearly_stats(self) -> dict[str, float]:
        """Yearly return statistics."""
        eq = self.equity_curve
        rf = self._config.risk_free_rate
        yearly = eq.resample("YE").last().pct_change().dropna()

        if len(yearly) < 2:
            return {
                "yearly_sharpe": 0.0, "yearly_sortino": 0.0,
                "yearly_mean": float(yearly.mean()) if len(yearly) > 0 else 0.0,
                "yearly_vol": 0.0,
                "yearly_skew": 0.0, "yearly_kurt": 0.0,
                "best_year": float(yearly.max()) if len(yearly) > 0 else 0.0,
                "worst_year": float(yearly.min()) if len(yearly) > 0 else 0.0,
            }

        excess = yearly - rf
        std = float(excess.std())
        downside = excess[excess < 0]
        down_std = float(downside.std()) if len(downside) > 0 else 0.0

        return {
            "yearly_sharpe": float(excess.mean()) / std if std > 0 else 0.0,
            "yearly_sortino": float(excess.mean()) / down_std if down_std > 0 else 0.0,
            "yearly_mean": float(yearly.mean()),
            "yearly_vol": float(yearly.std()),
            "yearly_skew": float(yearly.skew()),
            "yearly_kurt": float(yearly.kurt()),
            "best_year": float(yearly.max()),
            "worst_year": float(yearly.min()),
        }

    def _drawdown_analysis(self) -> dict[str, float]:
        """Drawdown episode analysis and win-rate metrics."""
        eq = self.equity_curve
        cummax = eq.cummax()
        drawdown = (eq - cummax) / cummax

        # Identify drawdown episodes (contiguous periods below cummax)
        in_dd = eq < cummax
        episodes: list[dict[str, Any]] = []
        current_start = None
        current_trough = 0.0

        for i, is_dd in enumerate(in_dd):
            if is_dd:
                if current_start is None:
                    current_start = i
                    current_trough = float(drawdown.iloc[i])
                else:
                    current_trough = min(current_trough, float(drawdown.iloc[i]))
            else:
                if current_start is not None:
                    start_dt = eq.index[current_start]
                    end_dt = eq.index[i]
                    days = (end_dt - start_dt).days
                    episodes.append({"trough": current_trough, "days": days})
                    current_start = None
                    current_trough = 0.0

        # Handle ongoing drawdown at end of series
        if current_start is not None:
            start_dt = eq.index[current_start]
            end_dt = eq.index[-1]
            days = (end_dt - start_dt).days
            episodes.append({"trough": current_trough, "days": days})

        avg_dd = float(np.mean([e["trough"] for e in episodes])) if episodes else 0.0
        avg_dd_days = float(np.mean([e["days"] for e in episodes])) if episodes else 0.0

        # Monthly return analysis
        monthly = eq.resample("ME").last().pct_change().dropna()
        up = monthly[monthly > 0]
        down = monthly[monthly < 0]
        avg_up_month = float(up.mean()) if len(up) > 0 else 0.0
        avg_down_month = float(down.mean()) if len(down) > 0 else 0.0

        # Win year %
        yearly = eq.resample("YE").last().pct_change().dropna()
        win_year_pct = float((yearly > 0).mean()) if len(yearly) > 0 else 0.0

        # Win 12-month rolling %
        if len(monthly) >= 13:
            rolling_12m = monthly.rolling(12).apply(
                lambda x: float(np.prod(1 + x) - 1), raw=True
            ).dropna()
            win_12m_pct = float((rolling_12m > 0).mean()) if len(rolling_12m) > 0 else 0.0
        else:
            win_12m_pct = 0.0

        return {
            "avg_drawdown": avg_dd,
            "avg_drawdown_days": avg_dd_days,
            "avg_up_month": avg_up_month,
            "avg_down_month": avg_down_month,
            "win_year_pct": win_year_pct,
            "win_12m_pct": win_12m_pct,
        }

    def plot(self, interactive: bool = False) -> Any:
        """Render equity curve and drawdown."""
        if interactive:
            return self._render_plotly()
        return self._render_matplotlib()

    def _render_matplotlib(self) -> Any:
        """Render per-asset equity, total equity, and drawdown using Matplotlib."""
        eq = self.equity_curve
        cummax = eq.cummax()
        drawdown = (eq - cummax) / cummax

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 7), sharex=True)

        # Per-asset lines if prices available
        asset_eq = self._per_asset_equity()
        for col in asset_eq.columns:
            if col == "total":
                continue
            ax1.plot(asset_eq.index, asset_eq[col], label=col, alpha=0.7)

        # Total equity (bold)
        ax1.plot(eq.index, eq.values, label="Total", color="black", linewidth=2)
        ax1.set_ylabel("Equity")
        ax1.set_title(f"{self.name} — Equity Curve")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2.fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color="red")
        ax2.set_ylabel("Drawdown")
        ax2.set_xlabel("Date")
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def _render_plotly(self) -> Any:
        """Render per-asset equity, total equity, and drawdown using Plotly."""
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            raise ImportError(
                "Plotly is required for interactive charts. "
                "Install it with: pip install plotly"
            ) from None

        eq = self.equity_curve
        cummax = eq.cummax()
        drawdown = (eq - cummax) / cummax

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            subplot_titles=[f"{self.name} — Equity Curve", "Drawdown"])

        # Per-asset lines
        asset_eq = self._per_asset_equity()
        for col in asset_eq.columns:
            if col == "total":
                continue
            fig.add_trace(go.Scatter(x=asset_eq.index, y=asset_eq[col], name=col), row=1, col=1)

        # Total equity (bold)
        fig.add_trace(go.Scatter(x=eq.index, y=eq.values, name="Total",
                                 line=dict(width=3, color="black")), row=1, col=1)
        fig.add_trace(go.Scatter(x=drawdown.index, y=drawdown.values, fill="tozeroy",
                                 name="Drawdown", line=dict(color="red")), row=2, col=1)
        fig.update_layout(height=700, width=1200)
        return fig

    def plot_security_weights(self) -> Any:
        """Render stacked area chart of portfolio weights over time."""
        if not self._weight_history:
            fig, ax = plt.subplots(figsize=(16, 4))
            ax.set_title(f"{self.name} — Security Weights (no rebalance data)")
            return fig

        df = pd.DataFrame(self._weight_history)
        pivot = df.pivot_table(index="date", columns="ticker", values="weight", fill_value=0.0)
        pivot = pivot.sort_index()

        fig, ax = plt.subplots(figsize=(16, 4))
        ax.stackplot(pivot.index, *[pivot[col].values for col in pivot.columns],
                     labels=pivot.columns)
        ax.set_ylabel("Weight")
        ax.set_title(f"{self.name} — Security Weights")
        ax.legend(loc="upper left")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_histogram(self) -> Any:
        """Render histogram of daily returns."""
        returns = self.equity_curve.pct_change().dropna()

        fig, ax = plt.subplots(figsize=(16, 4))
        ax.hist(returns.values, bins=50, alpha=0.7, edgecolor="black")
        ax.set_xlabel("Daily Return")
        ax.set_ylabel("Frequency")
        ax.set_title(f"{self.name} — Return Distribution")
        ax.axvline(0, color="red", linestyle="--", alpha=0.5)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    # ------------------------------------------------------------------
    # Interactive Plotly chart
    # ------------------------------------------------------------------

    def _per_asset_equity(self) -> pd.DataFrame:
        """Reconstruct per-asset equity from trade records and prices.

        Returns a DataFrame indexed by date with one column per ticker
        plus a 'total' column from the equity curve.
        """
        eq = self.equity_curve
        if not self._trade_records or not self._prices:
            return pd.DataFrame({"total": eq})

        # Build positions snapshot: (date, ticker) → qty_after
        records = pd.DataFrame(self._trade_records)
        if records.empty:
            return pd.DataFrame({"total": eq})

        positions = records.pivot_table(
            index="date", columns="ticker", values="qty_after", aggfunc="last",
        )
        # Reindex to full equity curve dates and forward-fill quantities
        positions = positions.reindex(eq.index).ffill().fillna(0.0)

        # Multiply qty × close price per ticker
        asset_values = pd.DataFrame(index=eq.index)
        for ticker in positions.columns:
            if ticker in self._prices:
                close = self._prices[ticker]["close"].reindex(eq.index).ffill()
                asset_values[ticker] = positions[ticker] * close
            else:
                asset_values[ticker] = 0.0

        asset_values["total"] = eq
        return asset_values

    def plot_interactive(self) -> Any:
        """Render interactive Plotly chart with per-asset equity, trade markers, and drawdown.

        Returns a plotly.graph_objects.Figure. Save as PNG with fig.write_image().
        """
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            raise ImportError(
                "Plotly is required for interactive charts. "
                "Install it with: pip install plotly"
            ) from None

        asset_eq = self._per_asset_equity()
        tickers = [c for c in asset_eq.columns if c != "total"]

        # Build per-date trade info for hover text on rebalance dates
        trade_text_by_date: dict[pd.Timestamp, str] = {}
        if self._trade_records:
            records_df = pd.DataFrame(self._trade_records)
            nonzero = records_df[records_df["delta"].abs() > 1e-9]
            for date, grp in nonzero.groupby("date"):
                parts = []
                for _, t in grp.iterrows():
                    action = "BUY" if t["delta"] > 0 else "SELL"
                    parts.append(f"{action} {t['ticker']} ${t['price']:.2f} × {abs(t['delta']):.2f}")
                trade_text_by_date[date] = "<br>".join(parts)

        # Build custom hover text per date for equity lines
        hover_texts: dict[str, list[str]] = {col: [] for col in tickers + ["total"]}
        for date in asset_eq.index:
            total = asset_eq.loc[date, "total"]
            trade_line = trade_text_by_date.get(date, "")

            for col in tickers:
                val = asset_eq.loc[date, col]
                pct = val / total * 100 if total > 0 else 0
                hover_texts[col].append(f"{col}: ${val:,.0f} ({pct:.1f}%)")

            total_txt = f"Total: ${total:,.0f}"
            if trade_line:
                total_txt += f"<br>--- trades ---<br>{trade_line}"
            hover_texts["total"].append(total_txt)

        # Two rows: equity chart + drawdown
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25],
            vertical_spacing=0.05,
            subplot_titles=[f"{self.name} — Portfolio Breakdown", "Drawdown"],
        )

        # Per-asset lines (row 1)
        for col in tickers:
            fig.add_trace(go.Scatter(
                x=asset_eq.index, y=asset_eq[col],
                name=col, mode="lines",
                text=hover_texts[col],
                hovertemplate="%{x|%Y-%m-%d}<br>%{text}<extra></extra>",
            ), row=1, col=1)

        # Total equity line (bold)
        fig.add_trace(go.Scatter(
            x=asset_eq.index, y=asset_eq["total"],
            name="Total", mode="lines",
            line=dict(width=3, color="black"),
            text=hover_texts["total"],
            hovertemplate="%{x|%Y-%m-%d}<br>%{text}<extra></extra>",
        ), row=1, col=1)

        # Trade markers on per-asset lines (visual only, no hover)
        if self._trade_records:
            self._add_trade_markers(fig, asset_eq)

        # Drawdown subplot (row 2)
        eq = self.equity_curve
        cummax = eq.cummax()
        drawdown = (eq - cummax) / cummax
        fig.add_trace(go.Scatter(
            x=drawdown.index, y=drawdown.values,
            fill="tozeroy", name="Drawdown",
            line=dict(color="red", width=1),
            fillcolor="rgba(255, 0, 0, 0.2)",
            hovertemplate="%{x|%Y-%m-%d}<br>Drawdown: %{y:.2%}<extra></extra>",
            showlegend=False,
        ), row=2, col=1)

        fig.update_layout(
            yaxis_title="Value ($)",
            yaxis2_title="Drawdown",
            yaxis2_tickformat=".0%",
            xaxis2_title="Date",
            hovermode="x unified",
            height=700, width=1200,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        return fig

    def _add_trade_markers(self, fig: Any, asset_eq: pd.DataFrame) -> None:
        """Add buy/sell triangle markers on per-asset lines (visual only, excluded from hover)."""
        import plotly.graph_objects as go

        records = pd.DataFrame(self._trade_records)
        if records.empty:
            return

        records = records[records["delta"].abs() > 1e-9].copy()
        if records.empty:
            return

        buys = records[records["delta"] > 0]
        sells = records[records["delta"] < 0]

        def _asset_y(rows: pd.DataFrame) -> list[float]:
            result = []
            for _, r in rows.iterrows():
                ticker = r["ticker"]
                date = r["date"]
                if ticker in asset_eq.columns:
                    result.append(float(asset_eq[ticker].asof(date)))
                else:
                    result.append(float(asset_eq["total"].asof(date)))
            return result

        if not buys.empty:
            buy_y = _asset_y(buys)
            fig.add_trace(go.Scatter(
                x=buys["date"], y=buy_y,
                mode="markers", name="Buy",
                marker=dict(symbol="triangle-up", size=9, color="green"),
                hoverinfo="skip",
            ), row=1, col=1)
            for d, y in zip(buys["date"], buy_y):
                fig.add_shape(
                    type="line", x0=d, x1=d, y0=0, y1=y,
                    line=dict(color="green", dash="dot", width=1),
                    opacity=0.3, row=1, col=1,
                )

        if not sells.empty:
            sell_y = _asset_y(sells)
            fig.add_trace(go.Scatter(
                x=sells["date"], y=sell_y,
                mode="markers", name="Sell",
                marker=dict(symbol="triangle-down", size=9, color="red"),
                hoverinfo="skip",
            ), row=1, col=1)
            for d, y in zip(sells["date"], sell_y):
                fig.add_shape(
                    type="line", x0=d, x1=d, y0=0, y1=y,
                    line=dict(color="red", dash="dot", width=1),
                    opacity=0.3, row=1, col=1,
                )


class BacktestResult:
    """Collection of backtest results. Always wraps a list, even for single backtests."""

    def __init__(self, results: list[_SingleResult]) -> None:
        self._results = results
        self._name_map = {r.name: r for r in results}

    def __getitem__(self, key: int | str) -> _SingleResult:
        if isinstance(key, int):
            return self._results[key]
        if isinstance(key, str):
            if key not in self._name_map:
                raise KeyError(f"No backtest named '{key}'")
            return self._name_map[key]
        raise TypeError(f"Key must be int or str, got {type(key)}")

    def __len__(self) -> int:
        return len(self._results)

    def summary(self) -> pd.DataFrame:
        """Summary across all backtests. For single result, delegates directly."""
        if len(self._results) == 1:
            return self._results[0].summary()
        frames = {r.name: r.summary()["value"] for r in self._results}
        return pd.DataFrame(frames)

    def full_summary(self) -> pd.DataFrame:
        """Full summary across all backtests."""
        if len(self._results) == 1:
            return self._results[0].full_summary()
        frames = {r.name: r.full_summary()["value"] for r in self._results}
        return pd.DataFrame(frames)

    def plot(self, interactive: bool = False) -> Any:
        """Plot all backtest equity curves."""
        if len(self._results) == 1:
            return self._results[0].plot(interactive=interactive)
        if interactive:
            try:
                import plotly.graph_objects as go
            except ImportError:
                raise ImportError(
                    "Plotly is required for interactive charts. "
                    "Install it with: pip install plotly"
                ) from None
            fig = go.Figure()
            for r in self._results:
                fig.add_trace(go.Scatter(x=r.equity_curve.index, y=r.equity_curve.values, name=r.name))
            fig.update_layout(title="Backtest Comparison", yaxis_title="Equity", height=700, width=1200)
            return fig
        fig, ax = plt.subplots(figsize=(16, 5))
        for r in self._results:
            ax.plot(r.equity_curve.index, r.equity_curve.values, label=r.name)
        ax.set_ylabel("Equity")
        ax.set_title("Backtest Comparison")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_security_weights(self) -> Any:
        """Plot security weights for all backtests."""
        if len(self._results) == 1:
            return self._results[0].plot_security_weights()
        # Multi: side-by-side subplots
        n = len(self._results)
        fig, axes = plt.subplots(n, 1, figsize=(16, 4 * n), sharex=True)
        if n == 1:
            axes = [axes]
        for ax, r in zip(axes, self._results):
            if r._weight_history:
                df = pd.DataFrame(r._weight_history)
                pivot = df.pivot_table(index="date", columns="ticker", values="weight", fill_value=0.0).sort_index()
                ax.stackplot(pivot.index, *[pivot[col].values for col in pivot.columns], labels=pivot.columns)
                ax.legend(loc="upper left")
            ax.set_title(f"{r.name} — Security Weights")
            ax.set_ylabel("Weight")
            ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_histogram(self) -> Any:
        """Plot return distribution for all backtests."""
        if len(self._results) == 1:
            return self._results[0].plot_histogram()
        fig, ax = plt.subplots(figsize=(16, 4))
        for r in self._results:
            returns = r.equity_curve.pct_change().dropna()
            ax.hist(returns.values, bins=50, alpha=0.5, label=r.name, edgecolor="black")
        ax.set_xlabel("Daily Return")
        ax.set_ylabel("Frequency")
        ax.set_title("Return Distribution Comparison")
        ax.axvline(0, color="red", linestyle="--", alpha=0.5)
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_interactive(self) -> Any:
        """Interactive Plotly chart. Single: per-asset + trades. Multi: overlaid totals + trades."""
        if len(self._results) == 1:
            return self._results[0].plot_interactive()
        return self._plot_interactive_multi()

    def _plot_interactive_multi(self) -> Any:
        """Multi-backtest interactive comparison chart with drawdown."""
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            raise ImportError(
                "Plotly is required for interactive charts. "
                "Install it with: pip install plotly"
            ) from None

        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25],
            vertical_spacing=0.05,
            subplot_titles=["Strategy Comparison", "Drawdown"],
        )
        colours = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
        ]

        for i, r in enumerate(self._results):
            colour = colours[i % len(colours)]
            eq = r.equity_curve

            # Total equity line per strategy (row 1) — no hover on lines
            fig.add_trace(go.Scatter(
                x=eq.index, y=eq.values,
                name=r.name, mode="lines",
                line=dict(width=2, color=colour),
                legendgroup=r.name,
                hoverinfo="none",
            ), row=1, col=1)

            # Trade markers per strategy on equity line
            if r._trade_records:
                records = pd.DataFrame(r._trade_records)
                records = records[records["delta"].abs() > 1e-9]
                buys = records[records["delta"] > 0]
                sells = records[records["delta"] < 0]

                if not buys.empty:
                    buy_y = [float(eq.asof(d)) for d in buys["date"]]
                    fig.add_trace(go.Scatter(
                        x=buys["date"], y=buy_y,
                        mode="markers", name=f"{r.name} Buy",
                        marker=dict(symbol="triangle-up", size=8, color=colour, line=dict(color="green", width=1)),
                        legendgroup=r.name, showlegend=False,
                        text=[f"{r.name} BUY {row['ticker']}<br>${row['price']:.2f} × {row['delta']:.2f}" for _, row in buys.iterrows()],
                        hovertemplate="%{x|%Y-%m-%d}<br>%{text}<extra></extra>",
                    ), row=1, col=1)

                if not sells.empty:
                    sell_y = [float(eq.asof(d)) for d in sells["date"]]
                    fig.add_trace(go.Scatter(
                        x=sells["date"], y=sell_y,
                        mode="markers", name=f"{r.name} Sell",
                        marker=dict(symbol="triangle-down", size=8, color=colour, line=dict(color="red", width=1)),
                        legendgroup=r.name, showlegend=False,
                        text=[f"{r.name} SELL {row['ticker']}<br>${row['price']:.2f} × {abs(row['delta']):.2f}" for _, row in sells.iterrows()],
                        hovertemplate="%{x|%Y-%m-%d}<br>%{text}<extra></extra>",
                    ), row=1, col=1)

            # Drawdown per strategy (row 2) — no hover
            cummax = eq.cummax()
            drawdown = (eq - cummax) / cummax
            fig.add_trace(go.Scatter(
                x=drawdown.index, y=drawdown.values,
                name=f"{r.name} DD", mode="lines",
                line=dict(width=1, color=colour),
                legendgroup=r.name, showlegend=False,
                hoverinfo="none",
            ), row=2, col=1)

        fig.update_layout(
            yaxis_title="Value ($)",
            yaxis2_title="Drawdown",
            yaxis2_tickformat=".0%",
            xaxis2_title="Date",
            hovermode="closest",
            height=700, width=1200,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        return fig
