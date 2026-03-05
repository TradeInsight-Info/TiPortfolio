"""BetaScreenerStrategy: dynamic long/short selection by rolling OLS beta."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class BetaScreenerStrategy:
    """Dynamic long/short allocation that ranks a stock universe by rolling beta each rebalance.

    At each rebalance date:
    1. Computes OLS beta (β_i = Cov(r_i, r_bench) / Var(r_bench)) for every symbol in `universe`
       using the last `lookback_days` rows of `prices_history` from context.
    2. Selects `n_long` lowest-beta symbols as the long book and `n_short` highest-beta symbols
       as the short book.
    3. Sizes books so Σ(w_i × β_i) ≈ 0 by scaling the short book:
         short_book_size = book_size × avg_beta_long / avg_beta_short  (clamped 0.1–2.0)
    4. Assigns equal weight within each book; all other universe symbols get weight 0.0.
    5. Residual weight absorbed by `cash_symbol`.

    `get_symbols()` returns the full `universe + [cash_symbol]` so the engine fetches and
    tracks prices for every candidate stock throughout the backtest.

    `benchmark_prices` must be an OHLCV DataFrame with a `close` column (or single column)
    covering the backtest date range — pass SPY prices pre-fetched at notebook setup.
    """

    universe: list[str]
    n_long: int
    n_short: int
    cash_symbol: str
    benchmark_prices: pd.DataFrame
    lookback_days: int = 60
    book_size: float = 0.5

    def __post_init__(self) -> None:
        if self.cash_symbol in self.universe:
            raise ValueError(
                f"BetaScreenerStrategy: cash_symbol {self.cash_symbol!r} must not be in universe"
            )
        if self.n_long + self.n_short > len(self.universe):
            raise ValueError(
                f"BetaScreenerStrategy: n_long ({self.n_long}) + n_short ({self.n_short}) "
                f"exceeds universe size ({len(self.universe)})"
            )

    def get_symbols(self) -> list[str]:
        return list(self.universe) + [self.cash_symbol]

    def _equal_weight_fallback(self) -> dict[str, float]:
        """Equal-weight fallback: equal long weights, equal short weights, cash absorbs net."""
        n_long = self.n_long
        n_short = self.n_short
        # Use first n_long as longs and last n_short as shorts (arbitrary but deterministic)
        longs = self.universe[:n_long]
        shorts = self.universe[-n_short:]
        weights: dict[str, float] = {s: 0.0 for s in self.universe}
        for s in longs:
            weights[s] = self.book_size / n_long
        for s in shorts:
            weights[s] = -self.book_size / n_short
        net = sum(weights.values())
        weights[self.cash_symbol] = 1.0 - net
        return weights

    def _get_benchmark_returns(self, prices_history: pd.DataFrame) -> pd.Series | None:
        """Extract benchmark returns aligned to prices_history index."""
        bp = self.benchmark_prices
        ser = bp["close"] if "close" in bp.columns else bp.iloc[:, 0]
        # Normalize index timezone and unit to match prices_history
        ph_idx = prices_history.index
        if hasattr(ph_idx, "tz") and ph_idx.tz is not None:
            if ser.index.tz is None:
                ser = ser.copy()
                ser.index = ser.index.tz_localize("UTC")
            else:
                ser = ser.copy()
                ser.index = ser.index.tz_convert("UTC")
        try:
            ser = ser.copy()
            ser.index = pd.DatetimeIndex(ser.index).as_unit("ns")
        except Exception:
            pass
        bench = ser.reindex(ph_idx, method="ffill").dropna()
        returns = bench.pct_change().dropna()
        return returns if len(returns) >= 2 else None

    def _compute_betas(self, prices_history: pd.DataFrame) -> dict[str, float] | None:
        """Compute rolling OLS beta for every universe symbol. Returns None on insufficient data."""
        if len(prices_history) < self.lookback_days + 1:
            return None

        bench_returns = self._get_benchmark_returns(prices_history)
        if bench_returns is None:
            return None

        hist = prices_history[self.universe].tail(self.lookback_days + 1)
        sym_returns = hist.pct_change().dropna()

        common_idx = sym_returns.index.intersection(bench_returns.index)
        if len(common_idx) < 5:
            return None

        sym_returns = sym_returns.loc[common_idx]
        bench_aligned = bench_returns.loc[common_idx]
        bench_var = float(bench_aligned.var(ddof=1))
        if bench_var == 0.0:
            return None

        betas: dict[str, float] = {}
        for s in self.universe:
            cov = float(sym_returns[s].cov(bench_aligned))
            betas[s] = cov / bench_var
        return betas

    def get_target_weights(
        self,
        date: pd.Timestamp,
        total_equity: float,
        positions_dollars: dict[str, float],
        prices_row: pd.Series,
        **context: Any,
    ) -> dict[str, float]:
        prices_history: pd.DataFrame | None = context.get("prices_history")
        if prices_history is None:
            warnings.warn("BetaScreenerStrategy: prices_history not in context; using equal-weight fallback", UserWarning)
            return self._equal_weight_fallback()

        betas = self._compute_betas(prices_history)
        if betas is None:
            warnings.warn(
                f"BetaScreenerStrategy: insufficient history or benchmark data at {date}; using equal-weight fallback",
                UserWarning,
            )
            return self._equal_weight_fallback()

        # Rank universe by beta
        ranked = sorted(betas.items(), key=lambda kv: kv[1])
        long_book = [s for s, _ in ranked[: self.n_long]]
        short_book = [s for s, _ in ranked[-self.n_short :]]

        avg_beta_long = float(np.mean([betas[s] for s in long_book]))
        avg_beta_short = float(np.mean([betas[s] for s in short_book]))

        # Scale short book so Σ(w_i * β_i) ≈ 0
        if abs(avg_beta_short) < 1e-10:
            warnings.warn("BetaScreenerStrategy: avg_beta_short ≈ 0; using equal-weight fallback", UserWarning)
            return self._equal_weight_fallback()

        raw_sbs = self.book_size * avg_beta_long / avg_beta_short
        sbs = float(np.clip(raw_sbs, 0.1, 2.0))

        weights: dict[str, float] = {s: 0.0 for s in self.universe}
        for s in long_book:
            weights[s] = self.book_size / self.n_long
        for s in short_book:
            weights[s] = -sbs / self.n_short

        net = sum(weights.values())
        weights[self.cash_symbol] = 1.0 - net
        return weights
