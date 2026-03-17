"""Data-driven quantitative allocation strategies."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from tiportfolio.allocation.base import AllocationStrategy


@dataclass
class VolatilityTargeting(AllocationStrategy):
    """Long-only strategy: weights ∝ 1/realized_vol per asset, normalized to sum to 1.0.

    Optionally applies a target_vol scaling step that de-levers when portfolio
    volatility exceeds target_vol.  Weights are clamped to [0, 1.0] (long-only).
    Requires prices_history in context (injected by run_backtest); falls back to
    equal weights with a warning when history is missing or insufficient.
    """

    symbols: list[str]
    lookback_days: int
    target_vol: float | None = None

    def get_symbols(self) -> list[str]:
        return list(self.symbols)

    def get_target_weights(
        self,
        date: pd.Timestamp,
        total_equity: float,
        positions_dollars: dict[str, float],
        prices_row: pd.Series,
        **context: Any,
    ) -> dict[str, float]:
        n = len(self.symbols)
        equal: dict[str, float] = {s: 1.0 / n for s in self.symbols}

        prices_history: pd.DataFrame | None = context.get("prices_history")
        if prices_history is None:
            warnings.warn("VolatilityTargeting: prices_history not in context; using equal weights", UserWarning)
            return equal

        if len(prices_history) < self.lookback_days + 1:
            warnings.warn(
                f"VolatilityTargeting: insufficient history ({len(prices_history)} rows < {self.lookback_days + 1}); using equal weights",
                UserWarning,
            )
            return equal

        hist = prices_history[self.symbols].tail(self.lookback_days + 1)
        returns = hist.pct_change().dropna()
        if len(returns) == 0:
            warnings.warn("VolatilityTargeting: no returns computed; using equal weights", UserWarning)
            return equal

        # Annualized realized volatility
        vols: pd.Series = returns.std(ddof=1) * np.sqrt(252)
        if (vols <= 0).any() or vols.isna().any():
            warnings.warn("VolatilityTargeting: zero or NaN volatility; using equal weights", UserWarning)
            return equal

        # Inverse-vol weights, normalized
        inv_vols = 1.0 / vols
        raw_weights: pd.Series = inv_vols / inv_vols.sum()

        if self.target_vol is not None:
            # Portfolio vol via diagonal covariance approximation
            port_vol = float(np.sqrt((raw_weights.values**2 * vols.values**2).sum()))
            if port_vol > self.target_vol:
                scalar = min(self.target_vol / port_vol, 1.0)
                raw_weights = raw_weights * scalar
            # else: weights unchanged (already sum to 1.0)

        return raw_weights.to_dict()


@dataclass
class DollarNeutral(AllocationStrategy):
    """Long-short strategy with fixed intra-book ratios and tolerance-band rebalancing.

    Maintains net dollar exposure near zero by keeping long and short books of
    equal size (configurable via book_size).  Requires a cash_symbol to absorb
    residual capital so weights always sum to 1.0.

    long_weights / short_weights must each sum to 1.0 and must not overlap with
    each other or with cash_symbol.

    target weights:
        long  symbol i:  book_size * long_weights[i]
        short symbol j: -book_size * short_weights[j]
        cash:            1.0 - net_long_minus_short  (= 1.0 when balanced)

    When |long_value - short_value| / total_equity <= tolerance AND positions
    are non-empty, the strategy returns the current weights (no trades).
    """

    long_weights: dict[str, float]
    short_weights: dict[str, float]
    cash_symbol: str
    book_size: float = 0.5
    tolerance: float = 0.05
    long_book_size: float | None = None
    short_book_size: float | None = None

    def __post_init__(self) -> None:
        long_sum = sum(self.long_weights.values())
        if not (0.99 <= long_sum <= 1.01):
            raise ValueError(f"DollarNeutral: long_weights must sum to 1.0; got {long_sum:.4f}")
        short_sum = sum(self.short_weights.values())
        if not (0.99 <= short_sum <= 1.01):
            raise ValueError(f"DollarNeutral: short_weights must sum to 1.0; got {short_sum:.4f}")
        long_syms = set(self.long_weights)
        short_syms = set(self.short_weights)
        overlap = long_syms & short_syms
        if overlap:
            raise ValueError(f"DollarNeutral: long_weights and short_weights share symbols: {sorted(overlap)}")
        if self.cash_symbol in long_syms:
            raise ValueError(f"DollarNeutral: cash_symbol {self.cash_symbol!r} is in long_weights")
        if self.cash_symbol in short_syms:
            raise ValueError(f"DollarNeutral: cash_symbol {self.cash_symbol!r} is in short_weights")

    def get_symbols(self) -> list[str]:
        return list(self.long_weights) + list(self.short_weights) + [self.cash_symbol]

    def _target_weights(self) -> dict[str, float]:
        lbs = self.long_book_size if self.long_book_size is not None else self.book_size
        sbs = self.short_book_size if self.short_book_size is not None else self.book_size
        weights: dict[str, float] = {}
        for s, w in self.long_weights.items():
            weights[s] = lbs * w
        for s, w in self.short_weights.items():
            weights[s] = -sbs * w
        net = sum(weights.values())
        weights[self.cash_symbol] = 1.0 - net
        return weights

    def get_target_weights(
        self,
        date: pd.Timestamp,
        total_equity: float,
        positions_dollars: dict[str, float],
        prices_row: pd.Series,
        **context: Any,
    ) -> dict[str, float]:
        # Initial allocation: positions empty or all zero
        if not positions_dollars or all(v == 0.0 for v in positions_dollars.values()):
            return self._target_weights()

        if total_equity == 0.0:
            return self._target_weights()

        long_value = sum(positions_dollars.get(s, 0.0) for s in self.long_weights)
        short_value = abs(sum(positions_dollars.get(s, 0.0) for s in self.short_weights))
        imbalance = abs(long_value - short_value) / total_equity

        if imbalance <= self.tolerance:
            # Within band — return current weights (no trades)
            return {s: positions_dollars.get(s, 0.0) / total_equity for s in self.get_symbols()}

        return self._target_weights()


@dataclass
class BetaNeutral(AllocationStrategy):
    """Long-short strategy targeting zero portfolio beta vs a benchmark.

    Uses OLS rolling beta: β_i = Cov(r_i, r_bench) / Var(r_bench).

    For two symbols (one long, one short): solved analytically so sum(w_i * β_i) = 0.
    For N symbols: equal-weight within each book.

    Requires a cash_symbol so weights sum to 1.0.  Falls back to equal-weight
    within books (with a warning) when history is insufficient or benchmark is
    unavailable.

    benchmark_prices: if provided (OHLCV DataFrame), used directly; otherwise
    fetch_prices is called and the result is cached on the instance.
    """

    long_symbols: list[str]
    short_symbols: list[str]
    cash_symbol: str
    benchmark_symbol: str = "SPY"
    benchmark_prices: pd.DataFrame | None = None
    lookback_days: int = 60
    book_size: float = 0.5
    _cached_benchmark: pd.Series | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        long_set = set(self.long_symbols)
        short_set = set(self.short_symbols)
        overlap = long_set & short_set
        if overlap:
            raise ValueError(f"BetaNeutral: long_symbols and short_symbols share symbols: {sorted(overlap)}")
        if self.cash_symbol in long_set:
            raise ValueError(f"BetaNeutral: cash_symbol {self.cash_symbol!r} is in long_symbols")
        if self.cash_symbol in short_set:
            raise ValueError(f"BetaNeutral: cash_symbol {self.cash_symbol!r} is in short_symbols")

    def get_symbols(self) -> list[str]:
        return list(self.long_symbols) + list(self.short_symbols) + [self.cash_symbol]

    def _equal_weight_fallback(self) -> dict[str, float]:
        weights: dict[str, float] = {}
        n_long = len(self.long_symbols)
        n_short = len(self.short_symbols)
        for s in self.long_symbols:
            weights[s] = self.book_size / n_long if n_long > 0 else 0.0
        for s in self.short_symbols:
            weights[s] = -self.book_size / n_short if n_short > 0 else 0.0
        net = sum(weights.values())
        weights[self.cash_symbol] = 1.0 - net
        return weights

    def _get_benchmark_returns(self, prices_history: pd.DataFrame) -> pd.Series | None:
        """Return benchmark return series aligned to prices_history index, or None on failure."""
        if self.benchmark_prices is not None:
            bp = self.benchmark_prices
            ser = bp["close"] if "close" in bp.columns else bp.iloc[:, 0]
            bench_ser = ser.reindex(prices_history.index, method="ffill").dropna()
        else:
            if self._cached_benchmark is None:
                try:
                    from tiportfolio.data import fetch_prices  # local import to avoid circular
                    start = prices_history.index[0]
                    end = prices_history.index[-1]
                    fetched = fetch_prices([self.benchmark_symbol], start=start, end=end)
                    df = fetched[self.benchmark_symbol]
                    self._cached_benchmark = df["close"] if "close" in df.columns else df.iloc[:, 0]
                except Exception:
                    return None
            bench_ser = self._cached_benchmark.reindex(prices_history.index, method="ffill").dropna()

        return bench_ser.pct_change().dropna()

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
            warnings.warn("BetaNeutral: prices_history not in context; using equal weights", UserWarning)
            return self._equal_weight_fallback()

        if len(prices_history) < self.lookback_days + 1:
            warnings.warn(
                f"BetaNeutral: insufficient history ({len(prices_history)} rows < {self.lookback_days + 1}); using equal weights",
                UserWarning,
            )
            return self._equal_weight_fallback()

        bench_returns = self._get_benchmark_returns(prices_history)
        if bench_returns is None:
            warnings.warn("BetaNeutral: benchmark prices unavailable; using equal weights", UserWarning)
            return self._equal_weight_fallback()

        all_syms = self.long_symbols + self.short_symbols
        hist = prices_history[all_syms].tail(self.lookback_days + 1)
        sym_returns = hist.pct_change().dropna()

        # Align to benchmark
        common_idx = sym_returns.index.intersection(bench_returns.index)
        sym_returns = sym_returns.loc[common_idx]
        bench_aligned = bench_returns.loc[common_idx]

        if len(bench_aligned) < 5:
            warnings.warn("BetaNeutral: insufficient aligned returns; using equal weights", UserWarning)
            return self._equal_weight_fallback()

        bench_var = float(bench_aligned.var(ddof=1))
        if bench_var == 0.0:
            warnings.warn("BetaNeutral: zero benchmark variance; using equal weights", UserWarning)
            return self._equal_weight_fallback()

        # OLS beta for each symbol
        betas: dict[str, float] = {}
        for s in all_syms:
            cov = float(sym_returns[s].cov(bench_aligned))
            betas[s] = cov / bench_var

        # Compute weights
        weights: dict[str, float] = {}
        if len(self.long_symbols) == 1 and len(self.short_symbols) == 1:
            L = self.long_symbols[0]
            S = self.short_symbols[0]
            beta_L = betas[L]
            beta_S = betas[S]
            denom = beta_L + beta_S
            if abs(denom) < 1e-10:
                warnings.warn("BetaNeutral: degenerate betas (sum ≈ 0); using equal weights", UserWarning)
                return self._equal_weight_fallback()
            # Zero-beta analytic: w_L * beta_L + w_S * beta_S = 0
            # with gross exposure w_L + |w_S| = 2 * book_size
            w_L = 2.0 * self.book_size * beta_S / denom
            w_S = -2.0 * self.book_size * beta_L / denom
            weights[L] = w_L
            weights[S] = w_S
        else:
            n_long = len(self.long_symbols)
            n_short = len(self.short_symbols)
            for s in self.long_symbols:
                weights[s] = self.book_size / n_long if n_long > 0 else 0.0
            for s in self.short_symbols:
                weights[s] = -self.book_size / n_short if n_short > 0 else 0.0

        net = sum(weights.values())
        weights[self.cash_symbol] = 1.0 - net
        return weights
