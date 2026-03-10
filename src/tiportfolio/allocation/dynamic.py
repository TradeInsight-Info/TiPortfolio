"""Data-driven quantitative allocation strategies."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class VolatilityTargeting:
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
        vols: pd.Series = returns.std(ddof=1) * np.sqrt(252)  # type: ignore[arg-type]
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
class DollarNeutral:
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
class BetaNeutral:
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

        bench_var = float(bench_aligned.var(ddof=1))  # type: ignore[arg-type]
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


@dataclass
class DollarNeutralDynamic(DollarNeutral):
    """Dollar-neutral long/short strategy with dynamic hedge ratio based on rolling volatility.
    
    This strategy extends the base DollarNeutral class by dynamically adjusting the
    long and short book sizes based on relative volatility between the two assets.
    The goal is to equalize risk contribution from both positions, improving
    risk-adjusted returns while maintaining market neutrality.
    
    **Rolling Volatility Calculation**:
    
    The strategy uses a rolling window of daily returns to compute annualized volatility:
    
    1. Daily returns: r_t = (P_t / P_{t-1}) - 1
    2. Rolling std: σ_rolling = std(r_t, window=N) for N trading days
    3. Annualized volatility: σ_ann = σ_rolling × √252
    
    where 252 is the typical number of trading days per year.
    
    **Dynamic Hedge Ratio Formula**:
    
    The hedge ratio is computed as the ratio of volatilities:
    
        ratio = σ_long / σ_short
    
    This ratio is then clamped to [min_ratio, max_ratio] to prevent extreme allocations.
    
    **Book Size Derivation**:
    
    From the hedge ratio, book sizes are derived to ensure equal risk contribution:
    
        long_book_size = 1 / (1 + ratio)
        short_book_size = ratio / (1 + ratio)
    
    When ratio = 1.0 (equal volatility), this yields 50/50 allocation.
    When ratio > 1.0 (long is more volatile), short book is larger to compensate.
    When ratio < 1.0 (short is more volatile), long book is larger to compensate.
    
    **Weight Calculation**:
    
    Final portfolio weights (summing to 1.0):
    
        w_long = long_book_size × long_intra_weight
        w_short = -short_book_size × short_intra_weight
        w_cash = 1.0 - (w_long + w_short)
    
    Attributes:
        dynamic_long_symbol: Symbol for the long position.
        dynamic_short_symbol: Symbol for the short position.
        prices_dict: Dictionary mapping symbols to OHLCV DataFrames.
        volatility_window: Rolling window size in trading days (default: 60).
        min_ratio: Minimum allowed hedge ratio (default: 0.5).
        max_ratio: Maximum allowed hedge ratio (default: 2.0).
        long_vol: Series of annualized rolling volatility for long asset.
        short_vol: Series of annualized rolling volatility for short asset.
        dynamic_ratio: Series of clamped hedge ratios over time.
    
    Example:
        >>> strategy = DollarNeutralDynamic(
        ...     long_weights={"V": 1.0},
        ...     short_weights={"MA": 1.0},
        ...     cash_symbol="BIL",
        ...     dynamic_long_symbol="V",
        ...     dynamic_short_symbol="MA",
        ...     prices_dict=prices,
        ...     volatility_window=60,
        ... )
        >>> weights = strategy.get_target_weights(date, equity, positions, prices_row)
    """
    
    dynamic_long_symbol: str
    dynamic_short_symbol: str
    prices_dict: dict[str, pd.DataFrame]
    volatility_window: int = 60
    min_ratio: float = 0.5
    max_ratio: float = 2.0
    long_vol: pd.Series | None = field(default=None, init=False, repr=False)
    short_vol: pd.Series | None = field(default=None, init=False, repr=False)
    dynamic_ratio: pd.Series | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        # Validate inputs similar to DollarNeutral
        long_sum = sum(self.long_weights.values())
        if not (0.99 <= long_sum <= 1.01):
            raise ValueError(f"DollarNeutralDynamic: long_weights must sum to 1.0; got {long_sum:.4f}")
        short_sum = sum(self.short_weights.values())
        if not (0.99 <= short_sum <= 1.01):
            raise ValueError(f"DollarNeutralDynamic: short_weights must sum to 1.0; got {short_sum:.4f}")
        
        long_syms = set(self.long_weights)
        short_syms = set(self.short_weights)
        overlap = long_syms & short_syms
        if overlap:
            raise ValueError(f"DollarNeutralDynamic: long_weights and short_weights share symbols: {sorted(overlap)}")
        if self.cash_symbol in long_syms:
            raise ValueError(f"DollarNeutralDynamic: cash_symbol {self.cash_symbol!r} is in long_weights")
        if self.cash_symbol in short_syms:
            raise ValueError(f"DollarNeutralDynamic: cash_symbol {self.cash_symbol!r} is in short_weights")
        
        # Pre-calculate volatility and ratio series
        self.long_vol, self.short_vol = self._calculate_volatility()
        self.dynamic_ratio = self._calculate_dynamic_ratio()
        
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
        
    def _calculate_volatility(self) -> tuple[pd.Series, pd.Series]:
        """Calculate annualized rolling volatility for both assets.
        
        Computes the rolling standard deviation of daily returns, annualized
        by multiplying by √252 (trading days per year).
        
        Formula:
            σ_annualized = std(daily_returns, window=N) × √252
        
        Returns:
            tuple: (long_volatility, short_volatility) as pandas Series
                indexed by date. First `volatility_window` values are NaN
                due to insufficient data for rolling calculation.
        """
        # Extract close prices and calculate daily returns
        long_prices = self.prices_dict[self.dynamic_long_symbol]['close']
        short_prices = self.prices_dict[self.dynamic_short_symbol]['close']
        
        long_returns = long_prices.pct_change()
        short_returns = short_prices.pct_change()
        
        # Calculate rolling volatility (annualized)
        long_vol = long_returns.rolling(window=self.volatility_window).std() * np.sqrt(252)
        short_vol = short_returns.rolling(window=self.volatility_window).std() * np.sqrt(252)
        
        return long_vol, short_vol
    
    def _calculate_dynamic_ratio(self) -> pd.Series:
        """Calculate dynamic hedge ratio from volatility series.
        
        The hedge ratio represents the relative volatility of the long asset
        to the short asset. It is clamped to [min_ratio, max_ratio] bounds
        to prevent extreme allocations during volatility spikes.
        
        Formula:
            raw_ratio = σ_long / σ_short
            ratio = clamp(raw_ratio, min_ratio, max_ratio)
        
        Returns:
            pandas Series: Clamped hedge ratio for each date. NaN values
                (from insufficient data) are preserved and handled in
                get_target_weights() by defaulting to 1.0.
        """
        raw_ratio = self.long_vol / self.short_vol
        return raw_ratio.clip(lower=self.min_ratio, upper=self.max_ratio)
    
    def get_target_weights(
        self,
        date: pd.Timestamp,
        total_equity: float,
        positions_dollars: dict[str, float],
        prices_row: pd.Series,
        **context: Any,
    ) -> dict[str, float]:
        """Compute target weights based on dynamic hedge ratio at the given date.
        
        On each rebalance date, this method:
        1. Looks up the pre-computed hedge ratio for the signal date
        2. Converts ratio to book sizes using inverse-volatility weighting
        3. Calculates final weights using DollarNeutral logic
        
        The signal_date from context (if provided) is used instead of the
        current date to allow for look-ahead bias prevention in backtests.
        
        Book Size Formulas:
            long_book_size = 1 / (1 + ratio)
            short_book_size = ratio / (1 + ratio)
        
        These formulas ensure that when ratio > 1 (long is more volatile),
        the short book is larger, and vice versa.
        
        Args:
            date: Current rebalance date (pd.Timestamp).
            total_equity: Total portfolio equity in dollars.
            positions_dollars: Current positions as {symbol: dollar_value}.
            prices_row: Current prices as pandas Series (unused here).
            **context: Additional context including:
                - signal_date: Date to look up ratio (defaults to `date`).
        
        Returns:
            dict: Target weights {symbol: weight} summing to 1.0.
                Long positions have positive weights, short positions
                have negative weights, cash absorbs the residual.
        """
        self._update_book_sizes_from_ratio(date, context)
        return super().get_target_weights(
            date, total_equity, positions_dollars, prices_row, **context
        )
    
    def _update_book_sizes_from_ratio(self, date: pd.Timestamp, context: dict[str, Any]) -> None:
        """Update long_book_size and short_book_size based on dynamic ratio.
        
        Args:
            date: Current date for ratio lookup.
            context: Context dictionary that may contain signal_date.
        """
        # Use signal_date from context if available, otherwise use current date
        signal_date = context.get('signal_date', date)
        
        # Handle timezone alignment for lookup
        lookup_date = signal_date.replace(tzinfo=None)
        
        # Find the ratio for the signal date
        if lookup_date in self.dynamic_ratio.index:
            ratio = self.dynamic_ratio.loc[lookup_date]
        else:
            # Ensure index is sorted for asof lookup
            if not self.dynamic_ratio.index.is_monotonic_increasing:
                self.dynamic_ratio = self.dynamic_ratio.sort_index()
            try:
                ratio = self.dynamic_ratio.asof(lookup_date)
            except Exception:
                ratio = 1.0
        
        # Handle NaN values by defaulting to equal allocation
        if pd.isna(ratio):
            ratio = 1.0
        
        # Update book sizes based on dynamic ratio
        # These formulas ensure proper risk contribution balancing
        self.long_book_size = 1.0 / (1.0 + ratio)
        self.short_book_size = ratio / (1.0 + ratio)
