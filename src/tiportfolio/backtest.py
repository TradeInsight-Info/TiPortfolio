from __future__ import annotations

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
        config: TiConfig | None = None,
    ) -> None:
        tickers = _leaf_ticker_names(portfolio)
        subset = {t: data[t] for t in tickers if t in data} if tickers else data
        validate_data(subset)
        self.portfolio = portfolio
        self.data = subset
        self.config = config or TiConfig()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_parent(portfolio: Portfolio) -> bool:
    return (
        portfolio.children is not None
        and len(portfolio.children) > 0
        and isinstance(portfolio.children[0], Portfolio)
    )


def _leaf_ticker_names(portfolio: Portfolio) -> list[str]:
    """Return flat list of ticker strings from a portfolio's leaf nodes."""
    if _is_parent(portfolio):
        result: list[str] = []
        for child in portfolio.children:  # type: ignore[union-attr]
            result.extend(_leaf_ticker_names(child))
        return result
    if portfolio.children and isinstance(portfolio.children[0], str):
        return list(portfolio.children)  # type: ignore[arg-type]
    return []



def _init_portfolio(portfolio: Portfolio, initial_capital: float) -> None:
    """Recursively initialise portfolio tree state."""
    portfolio.positions = {}
    if _is_parent(portfolio):
        portfolio.cash = initial_capital
        portfolio.equity = initial_capital
        for child in portfolio.children:  # type: ignore[union-attr]
            _init_portfolio(child, 0.0)
    else:
        portfolio.cash = initial_capital
        portfolio.equity = initial_capital


# ---------------------------------------------------------------------------
# Engine functions
# ---------------------------------------------------------------------------


def mark_to_market(
    portfolio: Portfolio,
    prices: dict[str, pd.DataFrame],
    date: pd.Timestamp,
) -> None:
    """Recompute portfolio equity. Recursive for parent nodes."""
    if _is_parent(portfolio):
        for child in portfolio.children:  # type: ignore[union-attr]
            mark_to_market(child, prices, date)
        portfolio.equity = portfolio.cash + sum(c.equity for c in portfolio.children)  # type: ignore[union-attr]
    else:
        position_value = sum(
            qty * prices[ticker].loc[date, "close"]
            for ticker, qty in portfolio.positions.items()
        )
        portfolio.equity = portfolio.cash + position_value


def deduct_daily_carry_costs(
    portfolio: Portfolio,
    prices: dict[str, pd.DataFrame],
    date: pd.Timestamp,
    config: TiConfig,
) -> None:
    """Deduct short borrow and leverage loan costs. Recursive for parents."""
    if _is_parent(portfolio):
        for child in portfolio.children:  # type: ignore[union-attr]
            deduct_daily_carry_costs(child, prices, date, config)
        return

    for ticker, qty in portfolio.positions.items():
        if qty == 0.0:
            continue
        price = prices[ticker].loc[date, "close"]
        # Short borrow cost
        if qty < 0:
            portfolio.cash -= abs(qty * price) * config.stock_borrow_rate / config.bars_per_year

    # Leverage cost: when total long value exceeds equity
    long_value = sum(
        qty * prices[t].loc[date, "close"]
        for t, qty in portfolio.positions.items()
        if qty > 0
    )
    if long_value > portfolio.equity:
        portfolio.cash -= (long_value - portfolio.equity) * config.loan_rate / config.bars_per_year


def _liquidate_child(
    child: Portfolio,
    prices: dict[str, pd.DataFrame],
    date: pd.Timestamp,
    config: TiConfig,
) -> None:
    """Sell all positions in a child, accumulate proceeds in child.cash."""
    for ticker, qty in list(child.positions.items()):
        price = prices[ticker].loc[date, "close"]
        fee = abs(qty) * config.fee_per_share
        child.cash += qty * price - fee
        del child.positions[ticker]


def allocate_equity_to_children(
    portfolio: Portfolio,
    context: Context,
) -> None:
    """4-step parent equity redistribution."""
    selected_names = {c.name for c in context.selected if isinstance(c, Portfolio)}

    # Step 1: Liquidate deselected children
    for child in portfolio.children:  # type: ignore[union-attr]
        if not isinstance(child, Portfolio):
            continue
        if child.name not in selected_names and child.positions:
            _liquidate_child(child, context.prices, context.date, context.config)
            child.equity = child.cash
            child.cash = 0.0

    # Step 2: Total available capital (children equity + parent's unallocated cash)
    total_equity = portfolio.cash + sum(c.equity for c in portfolio.children)  # type: ignore[union-attr]
    portfolio.cash = 0.0  # all capital now distributed to children

    # Step 3: Redistribute to selected children
    for child in context.selected:
        if not isinstance(child, Portfolio):
            continue
        fraction = context.weights.get(child.name, 0.0)
        target = total_equity * fraction
        # Adjust cash by the difference between target and current equity
        child.cash += target - child.equity
        child.equity = target

    # Step 4: Zero deselected children
    for child in portfolio.children:  # type: ignore[union-attr]
        if not isinstance(child, Portfolio):
            continue
        if child.name not in selected_names:
            child.equity = 0.0
            child.cash = 0.0


def execute_leaf_trades(
    portfolio: Portfolio,
    context: Context,
) -> list[dict[str, object]]:
    """Compute target positions from context.weights, trade the delta, deduct fees.

    Uses fractional shares (target_value / price).
    Returns a list of trade record dicts.
    """
    prices = context.prices
    date = context.date
    config = context.config
    equity_before = portfolio.equity

    new_positions: dict[str, float] = {}
    total_cost = 0.0
    total_fees = 0.0
    trade_records: list[dict[str, object]] = []

    for ticker in context.selected:
        if not isinstance(ticker, str):
            continue
        weight = context.weights.get(ticker, 0.0)
        price = prices[ticker].loc[date, "close"]
        if price <= 0:
            continue

        target_value = equity_before * weight
        target_qty = target_value / price  # fractional shares

        current_qty = portfolio.positions.get(ticker, 0.0)
        delta_qty = target_qty - current_qty
        cost = delta_qty * price
        fee = abs(delta_qty) * config.fee_per_share

        new_positions[ticker] = target_qty
        total_cost += cost
        total_fees += fee

        trade_records.append({
            "date": date,
            "portfolio": portfolio.name,
            "ticker": ticker,
            "qty_before": current_qty,
            "qty_after": target_qty,
            "delta": delta_qty,
            "price": float(price),
            "fee": fee,
            "equity_before": equity_before,
            "equity_after": 0.0,  # filled after settlement
        })

    # Close positions not in the new selection
    for ticker, qty in portfolio.positions.items():
        if ticker not in new_positions:
            price = prices[ticker].loc[date, "close"]
            fee = abs(qty) * config.fee_per_share
            portfolio.cash += qty * price - fee
            total_fees += fee

            trade_records.append({
                "date": date,
                "portfolio": portfolio.name,
                "ticker": ticker,
                "qty_before": qty,
                "qty_after": 0.0,
                "delta": -qty,
                "price": float(price),
                "fee": fee,
                "equity_before": equity_before,
                "equity_after": 0.0,
            })

    portfolio.positions = new_positions
    portfolio.cash -= total_cost + total_fees

    # Compute equity_after inline
    equity_after = portfolio.cash + sum(
        qty * float(prices[t].loc[date, "close"])
        for t, qty in portfolio.positions.items()
    )
    for rec in trade_records:
        rec["equity_after"] = equity_after

    return trade_records


def _evaluate_node(
    portfolio: Portfolio,
    context: Context,
) -> None:
    """Evaluate a portfolio's algo queue. Handles both leaf and parent nodes."""
    is_parent = _is_parent(portfolio)

    context.selected = list(portfolio.children or [])
    fired = portfolio.algo_queue(context)

    if is_parent and fired:
        for child in context.selected:
            if not isinstance(child, Portfolio):
                continue
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

    # Initialise portfolio tree
    _init_portfolio(portfolio, config.initial_capital)

    # Compute sorted union of all trading days
    all_dates: set[pd.Timestamp] = set()
    for df in prices.values():
        all_dates.update(df.index)
    trading_days = sorted(all_dates)

    equity_curve: list[tuple[pd.Timestamp, float]] = []
    all_trade_records: list[dict[str, object]] = []
    weight_history: list[dict[str, object]] = []

    # Wrapper to capture trade records from execute_leaf_trades
    def _recording_execute_leaf(port: Portfolio, ctx: Context) -> None:
        records = execute_leaf_trades(port, ctx)
        all_trade_records.extend(records)
        # Record weights at each rebalance
        for ticker, w in ctx.weights.items():
            weight_history.append({"date": ctx.date, "ticker": ticker, "weight": w})

    for date in trading_days:
        # 1. Mark-to-market
        mark_to_market(portfolio, prices, date)

        # 2. Daily carry costs
        deduct_daily_carry_costs(portfolio, prices, date, config)

        # 3. Record equity
        equity_curve.append((date, portfolio.equity))

        # 4. Evaluate algo queue
        context = Context(
            portfolio=portfolio,
            prices=prices,
            date=date,
            config=config,
            _execute_leaf=_recording_execute_leaf,
            _allocate_children=allocate_equity_to_children,
        )
        _evaluate_node(portfolio, context)

    # Build equity Series
    dates, values = zip(*equity_curve) if equity_curve else ([], [])
    equity_series = pd.Series(values, index=pd.DatetimeIndex(dates), name="equity")

    # Compute aggregate stats from trade records
    total_fee = sum(float(rec.get("fee", 0)) for rec in all_trade_records)
    rebalance_dates = {rec["date"] for rec in all_trade_records}
    rebalance_count = len(rebalance_dates)

    return _SingleResult(
        name=portfolio.name,
        equity_curve=equity_series,
        config=config,
        trade_records=all_trade_records,
        weight_history=weight_history,
        total_fee=total_fee,
        rebalance_count=rebalance_count,
        prices=prices,
    )


def _apply_leverage(
    result: _SingleResult, factor: float, config: TiConfig
) -> _SingleResult:
    """Scale equity curve by leverage factor with borrowing cost deduction."""
    if factor == 1.0:
        return result
    eq = result.equity_curve
    returns = eq.pct_change().fillna(0.0)
    daily_borrow_cost = (factor - 1) * config.loan_rate / config.bars_per_year
    leveraged_returns = returns * factor - daily_borrow_cost
    leveraged_eq = eq.iloc[0] * (1 + leveraged_returns).cumprod()
    leveraged_eq.iloc[0] = eq.iloc[0]
    name = f"{result.name} ({factor}x)"
    return _SingleResult(
        name=name,
        equity_curve=leveraged_eq,
        config=config,
        trade_records=result._trade_records,
        weight_history=result._weight_history,
        total_fee=result._total_fee,
        rebalance_count=result._rebalance_count,
        prices=result._prices,
        leverage=factor,
    )


def run(*tests: Backtest, leverage: float | list[float] = 1.0) -> BacktestResult:
    """Run one or more backtests and return a BacktestResult.

    Args:
        tests: One or more Backtest objects.
        leverage: Leverage multiplier. A single float applies to all backtests;
            a list applies per-backtest (must match length). Default 1.0.
    """
    if isinstance(leverage, list):
        if len(leverage) != len(tests):
            raise ValueError(
                f"leverage list length ({len(leverage)}) does not match "
                f"number of backtests ({len(tests)}): mismatch"
            )
        factors = leverage
    else:
        factors = [leverage] * len(tests)

    results = [
        _apply_leverage(_run_single(bt), factor, bt.config)
        for bt, factor in zip(tests, factors)
    ]
    return BacktestResult(results)
