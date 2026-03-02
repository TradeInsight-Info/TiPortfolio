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
    """AllocationStrategy that switches between high-vol and low-vol allocations by VIX level.

    When VIX >= target_vix + upper_bound use high_vol_allocation; when VIX <= target_vix + lower_bound
    use low_vol_allocation; in band use low_vol_allocation. Both sub-strategies must use the same symbols.
    """

    target_vix: float
    lower_bound: float
    upper_bound: float
    high_vol_allocation: AllocationStrategy
    low_vol_allocation: AllocationStrategy

    def __post_init__(self) -> None:
        validate_vix_regime_bounds(
            self.target_vix, self.lower_bound, self.upper_bound
        )
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
        vix_at_date = context.get("vix_at_date")
        if vix_at_date is None or (isinstance(vix_at_date, float) and pd.isna(vix_at_date)):
            return self.low_vol_allocation.get_target_weights(
                date, total_equity, positions_dollars, prices_row, **context
            )
        v = float(vix_at_date)
        upper_thresh = self.target_vix + self.upper_bound
        lower_thresh = self.target_vix + self.lower_bound
        if v >= upper_thresh:
            return self.high_vol_allocation.get_target_weights(
                date, total_equity, positions_dollars, prices_row, **context
            )
        if v <= lower_thresh:
            return self.low_vol_allocation.get_target_weights(
                date, total_equity, positions_dollars, prices_row, **context
            )
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
