from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TiConfig:
    """Global simulation parameters. Pass a custom instance to Backtest(config=...) to override."""

    fee_per_share: float = 0.0035
    risk_free_rate: float = 0.04
    loan_rate: float = 0.0514
    stock_borrow_rate: float = 0.07
    initial_capital: float = 10_000
    bars_per_year: int = 252
