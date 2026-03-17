"""Base allocation ABC and fixed-ratio strategy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pandas as pd


class AllocationStrategy(ABC):
    """Abstract base class for allocation strategies.
    
    To tell allocation of portfolio. Is it just fixed weights? Or something more complex like risk parity or mean-variance optimization?

    Subclasses implement get_symbols() and get_target_weights() to define how
    capital is allocated across assets at each rebalance date.

    Context keys injected by the backtest engine into ``**context``:

    Always available:
        prices_history (pd.DataFrame): Close-price history up to the signal date.
        signal_date (pd.Timestamp): Date the signal was generated (respects signal_delay).
        last_rebalance_date (pd.Timestamp | None): Date of the previous rebalance, or None.

    Only when using VolatilityBasedEngine:
        vix_at_date (float | None): VIX value at the signal date.
        use_high_vol_allocation (bool): True when VIX is in the high-volatility regime.
    """

    @abstractmethod
    def get_symbols(self) -> list[str]:
        """Return the list of symbols this strategy allocates to."""
        ...

    @abstractmethod
    def get_target_weights(
        self,
        date: pd.Timestamp,
        total_equity: float,
        positions_dollars: dict[str, float],
        prices_row: pd.Series,
        **context: Any,
    ) -> dict[str, float]:
        """Return target weights (symbol -> weight) that sum to 1.0."""
        ...


@dataclass
class FixRatio(AllocationStrategy):
    """Fixed weight allocation; implements AllocationStrategy. Keys must match prices dict keys."""

    weights: dict[str, float]

    def __post_init__(self) -> None:
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"weights must sum to 1.0; got sum={total}")

    def get_symbols(self) -> list[str]:
        return list(self.weights.keys())

    def get_target_weights(
        self,
        date: pd.Timestamp,
        total_equity: float,
        positions_dollars: dict[str, float],
        prices_row: pd.Series,
        **context: Any,
    ) -> dict[str, float]:
        return dict(self.weights)
