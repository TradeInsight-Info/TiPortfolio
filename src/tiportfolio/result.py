from __future__ import annotations

import math
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from tiportfolio.config import TiConfig


class _SingleResult:
    """Holds results for a single backtest."""

    def __init__(
        self,
        name: str,
        equity_curve: pd.Series,
        config: TiConfig,
    ) -> None:
        self.name = name
        self.equity_curve = equity_curve
        self._config = config

    def summary(self) -> pd.DataFrame:
        """Return a DataFrame with key performance metrics."""
        eq = self.equity_curve
        total_return = (eq.iloc[-1] / eq.iloc[0]) - 1.0

        # CAGR
        n_bars = len(eq)
        bars_per_year = self._config.bars_per_year
        years = n_bars / bars_per_year
        cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1.0 if years > 0 else 0.0

        # Max drawdown
        cummax = eq.cummax()
        drawdown = (eq - cummax) / cummax
        max_dd = drawdown.min()

        # Sharpe ratio
        returns = eq.pct_change().dropna()
        rf_per_bar = self._config.risk_free_rate / bars_per_year
        excess = returns - rf_per_bar
        sharpe = (
            excess.mean() / excess.std() * math.sqrt(bars_per_year)
            if excess.std() > 0
            else 0.0
        )

        data = {
            "total_return": total_return,
            "cagr": cagr,
            "max_drawdown": max_dd,
            "sharpe": sharpe,
        }
        return pd.DataFrame(
            {"value": data.values()},
            index=list(data.keys()),
        )

    def plot(self, interactive: bool = False) -> Any:
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
        # Multi-backtest: concat side by side
        frames = {r.name: r.summary()["value"] for r in self._results}
        return pd.DataFrame(frames)

    def plot(self, interactive: bool = False) -> Any:
        """Plot all backtest equity curves."""
        if len(self._results) == 1:
            return self._results[0].plot(interactive=interactive)
        fig, ax = plt.subplots(figsize=(12, 4))
        for r in self._results:
            ax.plot(r.equity_curve.index, r.equity_curve.values, label=r.name)
        ax.set_ylabel("Equity")
        ax.set_title("Backtest Comparison")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig
