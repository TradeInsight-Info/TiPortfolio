"""Base allocation protocol and fixed-ratio strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import pandas as pd


class AllocationStrategy(Protocol):
    """Protocol for allocation strategies: provide symbols and target weights at a point in time."""

    def get_symbols(self) -> list[str]:
        """Return the list of symbols this strategy allocates to."""
        ...

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
class FixRatio:
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
