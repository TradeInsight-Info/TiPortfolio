from __future__ import annotations

import math
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tiportfolio.config import TiConfig


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
    ) -> None:
        self.name = name
        self.equity_curve = equity_curve
        self._config = config
        self._trade_records = trade_records or []
        self._weight_history = weight_history or []
        self._total_fee = total_fee
        self._rebalance_count = rebalance_count

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
            "risk_free_rate": self._config.risk_free_rate,
            "total_return": total_return,
            "cagr": cagr,
            "sharpe": sharpe,
            "sortino": sortino,
            "max_drawdown": max_dd,
            "calmar": calmar,
            "kelly": kelly,
            "final_value": float(eq.iloc[-1]),
            "total_fee": self._total_fee,
            "rebalance_count": self._rebalance_count,
        }
        return pd.DataFrame(
            {"value": data.values()},
            index=list(data.keys()),
        )

    def full_summary(self) -> pd.DataFrame:
        """Return extended performance metrics. Superset of summary()."""
        eq = self.equity_curve
        bars_per_year = self._config.bars_per_year

        # Start with all summary metrics
        base = self.summary()
        data = {k: float(v) for k, v in base["value"].items()}

        # Max drawdown duration (bars from peak to recovery)
        cummax = eq.cummax()
        in_drawdown = eq < cummax
        max_dd_duration = 0
        current_duration = 0
        for is_dd in in_drawdown:
            if is_dd:
                current_duration += 1
                max_dd_duration = max(max_dd_duration, current_duration)
            else:
                current_duration = 0
        data["max_dd_duration"] = max_dd_duration

        # Monthly returns
        monthly = eq.resample("ME").last().pct_change().dropna()
        data["best_month"] = float(monthly.max()) if len(monthly) > 0 else 0.0
        data["worst_month"] = float(monthly.min()) if len(monthly) > 0 else 0.0
        data["win_rate"] = float((monthly > 0).mean()) if len(monthly) > 0 else 0.0

        return pd.DataFrame(
            {"value": data.values()},
            index=list(data.keys()),
        )

    def plot(self, interactive: bool = False) -> Any:
        """Render equity curve and drawdown."""
        if interactive:
            return self._render_plotly()
        return self._render_matplotlib()

    def _render_matplotlib(self) -> Any:
        """Render equity curve and drawdown using Matplotlib."""
        eq = self.equity_curve
        cummax = eq.cummax()
        drawdown = (eq - cummax) / cummax

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
        ax1.plot(eq.index, eq.values, label=self.name)
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
        """Render equity curve using Plotly."""
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
        fig.add_trace(go.Scatter(x=eq.index, y=eq.values, name=self.name), row=1, col=1)
        fig.add_trace(go.Scatter(x=drawdown.index, y=drawdown.values, fill="tozeroy",
                                 name="Drawdown", line=dict(color="red")), row=2, col=1)
        fig.update_layout(height=600)
        return fig

    def plot_security_weights(self) -> Any:
        """Render stacked area chart of portfolio weights over time."""
        if not self._weight_history:
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.set_title(f"{self.name} — Security Weights (no rebalance data)")
            return fig

        df = pd.DataFrame(self._weight_history)
        pivot = df.pivot_table(index="date", columns="ticker", values="weight", fill_value=0.0)
        pivot = pivot.sort_index()

        fig, ax = plt.subplots(figsize=(12, 4))
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

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.hist(returns.values, bins=50, alpha=0.7, edgecolor="black")
        ax.set_xlabel("Daily Return")
        ax.set_ylabel("Frequency")
        ax.set_title(f"{self.name} — Return Distribution")
        ax.axvline(0, color="red", linestyle="--", alpha=0.5)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig


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
            fig.update_layout(title="Backtest Comparison", yaxis_title="Equity", height=400)
            return fig
        fig, ax = plt.subplots(figsize=(12, 4))
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
        fig, axes = plt.subplots(n, 1, figsize=(12, 4 * n), sharex=True)
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
        fig, ax = plt.subplots(figsize=(10, 4))
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
