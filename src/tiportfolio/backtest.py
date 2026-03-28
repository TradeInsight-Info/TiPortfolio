from __future__ import annotations

import math
from dataclasses import replace

import pandas as pd

from tiportfolio.algo import Context
from tiportfolio.config import TiConfig
from tiportfolio.data import validate_data
from tiportfolio.portfolio import Portfolio
from tiportfolio.result import BacktestResult, _SingleResult


class Backtest:
    """Configures a backtest run. Validates data at construction time."""

    def __init__(
        self,
        portfolio: Portfolio,
        data: dict[str, pd.DataFrame],
        fee_per_share: float | None = None,
        config: TiConfig | None = None,
    ) -> None:
        validate_data(data)
        self.portfolio = portfolio
        self.data = data
        self.config = config or TiConfig()
        if fee_per_share is not None:
            self.config = replace(self.config, fee_per_share=fee_per_share)


# ---------------------------------------------------------------------------
# Engine functions
# ---------------------------------------------------------------------------


def mark_to_market(
    portfolio: Portfolio,
    prices: dict[str, pd.DataFrame],
    date: pd.Timestamp,
) -> None:
    """Recompute leaf portfolio equity from current positions and prices."""
    position_value = sum(
        qty * prices[ticker].loc[date, "close"]
        for ticker, qty in portfolio.positions.items()
    )
    portfolio.equity = portfolio.cash + position_value


def execute_leaf_trades(
    portfolio: Portfolio,
    context: Context,
) -> None:
    """Compute target positions from context.weights, trade the delta, deduct fees."""
    prices = context.prices
    date = context.date
    config = context.config
    equity = portfolio.equity

    new_positions: dict[str, float] = {}
    total_cost = 0.0
    total_fees = 0.0

    for ticker in context.selected:
        if not isinstance(ticker, str):
            continue
        weight = context.weights.get(ticker, 0.0)
        price = prices[ticker].loc[date, "close"]
        if price <= 0:
            continue

        target_value = equity * weight
        target_qty = math.floor(target_value / price)

        current_qty = portfolio.positions.get(ticker, 0.0)
        delta = target_qty - current_qty
        cost = delta * price
        fee = abs(delta) * config.fee_per_share

        new_positions[ticker] = target_qty
        total_cost += cost
        total_fees += fee

    # Close positions not in the new selection
    for ticker, qty in portfolio.positions.items():
        if ticker not in new_positions:
            price = prices[ticker].loc[date, "close"]
            cost = -qty * price  # sell all
            fee = abs(qty) * config.fee_per_share
            total_cost += cost
            total_fees += fee

    portfolio.positions = new_positions
    portfolio.cash -= total_cost + total_fees


def _evaluate_node(
    portfolio: Portfolio,
    context: Context,
) -> None:
    """Evaluate a portfolio's algo queue. Leaf-only for Chunk 1."""
    is_parent = (
        portfolio.children is not None
        and len(portfolio.children) > 0
        and isinstance(portfolio.children[0], Portfolio)
    )

    context.selected = list(portfolio.children or [])
    portfolio.algo_queue(context)

    if is_parent:
        for child in context.selected:
            child_context = Context(
                portfolio=child,
                prices=context.prices,
                date=context.date,
                config=context.config,
                _execute_leaf=context._execute_leaf,
                _allocate_children=context._allocate_children,
            )
            _evaluate_node(child, child_context)


def _run_single(backtest: Backtest) -> _SingleResult:
    """Execute a single backtest and return its result."""
    portfolio = backtest.portfolio
    prices = backtest.data
    config = backtest.config

    # Initialise portfolio state
    portfolio.cash = config.initial_capital
    portfolio.equity = config.initial_capital
    portfolio.positions = {}

    # Compute sorted union of all trading days
    all_dates: set[pd.Timestamp] = set()
    for df in prices.values():
        all_dates.update(df.index)
    trading_days = sorted(all_dates)

    equity_curve: list[tuple[pd.Timestamp, float]] = []

    for date in trading_days:
        # 1. Mark-to-market
        mark_to_market(portfolio, prices, date)

        # 2. Record equity
        equity_curve.append((date, portfolio.equity))

        # 3. Evaluate algo queue
        context = Context(
            portfolio=portfolio,
            prices=prices,
            date=date,
            config=config,
            _execute_leaf=execute_leaf_trades,
        )
        _evaluate_node(portfolio, context)

    # Build equity Series
    dates, values = zip(*equity_curve) if equity_curve else ([], [])
    equity_series = pd.Series(values, index=pd.DatetimeIndex(dates), name="equity")

    return _SingleResult(
        name=portfolio.name,
        equity_curve=equity_series,
        config=config,
    )


def run(*tests: Backtest) -> BacktestResult:
    """Run one or more backtests and return a BacktestResult."""
    results = [_run_single(bt) for bt in tests]
    return BacktestResult(results)
