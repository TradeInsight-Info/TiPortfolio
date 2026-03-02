"""Allocation strategies: protocol, fixed ratio, VIX regime, and filters."""

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


def validate_vix_regime_bounds(
    target_vix: float,
    lower_bound: float,
    upper_bound: float,
) -> None:
    """Raise ValueError if band params are inconsistent (e.g. lower > upper)."""
    if lower_bound > upper_bound:
        raise ValueError(
            f"vix_regime requires lower_bound <= upper_bound; got lower_bound={lower_bound}, upper_bound={upper_bound}"
        )


@dataclass
class VixRegimeAllocation:
    """AllocationStrategy that switches between high-vol and low-vol allocations based on engine decision.

    The engine determines whether to use high_vol_allocation or low_vol_allocation and passes
    this decision via the 'use_high_vol_allocation' context parameter. Both sub-strategies 
    must use the same symbols.
    """

    high_vol_allocation: AllocationStrategy
    low_vol_allocation: AllocationStrategy

    def __post_init__(self) -> None:
        high_syms = set(self.high_vol_allocation.get_symbols())
        low_syms = set(self.low_vol_allocation.get_symbols())
        if high_syms != low_syms:
            raise ValueError(
                f"VixRegimeAllocation: high_vol and low_vol must use same symbols; got {high_syms} vs {low_syms}"
            )

    def get_symbols(self) -> list[str]:
        return self.high_vol_allocation.get_symbols()

    def get_target_weights(
        self,
        date: pd.Timestamp,
        total_equity: float,
        positions_dollars: dict[str, float],
        prices_row: pd.Series,
        **context: Any,
    ) -> dict[str, float]:
        use_high_vol = context.get("use_high_vol_allocation", False)
        
        if use_high_vol:
            return self.high_vol_allocation.get_target_weights(
                date, total_equity, positions_dollars, prices_row, **context
            )
        else:
            return self.low_vol_allocation.get_target_weights(
                date, total_equity, positions_dollars, prices_row, **context
            )


class VixChangeFilter:
    """Rebalance only when VIX moved by delta_abs vs month ago or delta_pct vs last rebalance."""

    def __init__(
        self,
        *,
        delta_abs: float = 10.0,
        delta_pct: float = 0.20,
    ) -> None:
        self.delta_abs = delta_abs
        self.delta_pct = delta_pct

    def __call__(
        self,
        date: pd.Timestamp,
        vix_series: pd.Series,
        last_rebalance_date: pd.Timestamp | None,
    ) -> bool:
        vix_now = vix_series.asof(date) if hasattr(vix_series, "asof") else vix_series.get(date, float("nan"))
        if pd.isna(vix_now):
            return False
        month_ago = date - pd.DateOffset(months=1)
        vix_month_ago = vix_series.asof(month_ago) if hasattr(vix_series, "asof") else None
        if vix_month_ago is not None and not pd.isna(vix_month_ago):
            if abs(vix_now - vix_month_ago) >= self.delta_abs:
                return True
        if last_rebalance_date is not None:
            vix_last = vix_series.asof(last_rebalance_date) if hasattr(vix_series, "asof") else None
            if vix_last is not None and not pd.isna(vix_last) and vix_last != 0:
                if abs(vix_now - vix_last) / vix_last >= self.delta_pct:
                    return True
        return False
