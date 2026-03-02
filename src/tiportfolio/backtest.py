"""Backtest loop: run logic, rebalance decisions, and result types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from tiportfolio.allocation import AllocationStrategy
from tiportfolio.calendar import get_rebalance_dates
from tiportfolio.metrics import compute_metrics


@dataclass
class RebalanceDecision:
    """Record of a single rebalance: date, target weights, trades, fees, and prices (for quantity)."""

    date: pd.Timestamp
    equity_before: float
    equity_after: float
    target_weights: dict[str, float]
    trades_dollars: dict[str, float]
    fee_paid: float
    prices_at_rebalance: dict[str, float] = field(default_factory=dict)  # symbol -> price (for quantity)


@dataclass
class BacktestResult:
    """Result of a backtest run."""

    equity_curve: pd.Series
    metrics: dict[str, float]
    rebalance_decisions: list[RebalanceDecision] = field(default_factory=list)
    asset_curves: pd.DataFrame | None = None  # date index, one column per symbol (value in dollars)

    def summary(self) -> str:
        """Human-readable summary table."""
        m = self.metrics
        final_value = self.equity_curve.iloc[-1] if not self.equity_curve.empty else float('nan')
        lines = [
            "Backtest Summary",
            "----------------",
            f"Sharpe Ratio:    {m.get('sharpe_ratio', float('nan')):.4f}",
            f"CAGR:            {m.get('cagr', float('nan')):.2%}",
            f"Max Drawdown:    {m.get('max_drawdown', float('nan')):.2%}",
            f"MAR Ratio:       {m.get('mar_ratio', float('nan')):.4f}",
            f"Final Value:      {final_value:,.2f}",
            f"Rebalances:      {len(self.rebalance_decisions)}",
        ]
        return "\n".join(lines)


def run_backtest(
    prices_df: pd.DataFrame,
    allocation: AllocationStrategy,
    schedule_spec: str,
    fee_per_share: float,
    start: str | pd.Timestamp | None,
    end: str | pd.Timestamp | None,
    initial_value: float = 10000.0,
    rebalance_filter: Callable[
        [pd.Timestamp, pd.Series, pd.Timestamp | None], bool
    ] | None = None,
    vix_series: pd.Series | None = None,
    context_for_date: Callable[[pd.Timestamp], dict[str, Any]] | None = None,
    schedule_kwargs: dict[str, Any] | None = None,
) -> BacktestResult:
    """Core backtest: prices_df has date index and one column per symbol.

    allocation provides symbols and target weights via get_symbols/get_target_weights.
    context_for_date(date) is merged into context when calling get_target_weights.
    If rebalance_filter is set, rebalance only when filter(date, vix_series, last_rebalance_date) is True.
    schedule_kwargs is passed to get_rebalance_dates (e.g. vix_series, target_vix for vix_regime).
    """
    symbols = allocation.get_symbols()
    if start is not None:
        start = pd.Timestamp(start)
        if hasattr(prices_df.index, "tz") and prices_df.index.tz is not None:
            start = start.tz_localize(prices_df.index.tz) if start.tz is None else start
        prices_df = prices_df.loc[prices_df.index >= start]
    if end is not None:
        end = pd.Timestamp(end)
        if hasattr(prices_df.index, "tz") and prices_df.index.tz is not None:
            end = end.tz_localize(prices_df.index.tz) if end.tz is None else end
        prices_df = prices_df.loc[prices_df.index <= end]
    if prices_df.empty:
        return BacktestResult(
            equity_curve=pd.Series(dtype=float),
            metrics=compute_metrics(pd.Series(dtype=float)),
        )

    trading_dates = prices_df.index
    kwargs = schedule_kwargs or {}
    rebalance_dates = get_rebalance_dates(
        trading_dates, schedule_spec, start=start, end=end, **kwargs
    )
    rebalance_set = set(rebalance_dates)

    # Initial allocation on first date
    first_date = trading_dates[0]
    first_prices = prices_df.loc[first_date]
    initial_equity = float(initial_value)
    context0 = context_for_date(first_date) if context_for_date else {}
    weights0 = allocation.get_target_weights(
        first_date, initial_equity, {}, first_prices, **context0
    )
    positions_dollars: dict[str, float] = {}
    for sym in symbols:
        positions_dollars[sym] = initial_equity * weights0.get(sym, 0.0)
    equity_curve_list: list[tuple[pd.Timestamp, float]] = []
    asset_curve_rows: list[tuple[pd.Timestamp, dict[str, float]]] = []
    decisions: list[RebalanceDecision] = []
    last_rebalance_date: pd.Timestamp | None = None

    for i, date in enumerate(trading_dates):
        row = prices_df.loc[date]
        if i == 0:
            total_equity = initial_equity
        else:
            # Mark-to-market: update position values from previous close to this close
            prev_date = trading_dates[i - 1]
            prev_row = prices_df.loc[prev_date]
            for s in symbols:
                if prev_row[s] != 0 and not pd.isna(prev_row[s]):
                    ret = (row[s] - prev_row[s]) / prev_row[s]
                    positions_dollars[s] = positions_dollars[s] * (1 + ret)
            total_equity = sum(positions_dollars[s] for s in symbols)

            if date in rebalance_set:
                do_rebalance = True
                # For vix_regime, we don't use rebalance_filter - rebalance is determined by schedule kwargs
                if rebalance_filter is not None and vix_series is not None and schedule_spec != "vix_regime":
                    do_rebalance = rebalance_filter(date, vix_series, last_rebalance_date)
                
                if do_rebalance:
                    equity_before = total_equity
                    ctx = context_for_date(date) if context_for_date else {}
                    weights = allocation.get_target_weights(
                        date, total_equity, positions_dollars, row, **ctx
                    )
                    target_dollars = {s: total_equity * weights.get(s, 0.0) for s in symbols}
                    trades = {s: target_dollars[s] - positions_dollars[s] for s in symbols}
                    fee_paid = 0.0
                    for s in symbols:
                        price = float(row[s]) if row[s] and not pd.isna(row[s]) else 0.0
                        if price > 0:
                            trade_qty = trades[s] / price
                            fee_paid += abs(trade_qty) * fee_per_share
                    for s in symbols:
                        positions_dollars[s] = target_dollars[s]
                    total_equity = sum(positions_dollars[s] for s in symbols) - fee_paid
                    last_rebalance_date = date
                    if len(symbols) > 1:
                        decisions.append(
                            RebalanceDecision(
                                date=date,
                                equity_before=equity_before,
                                equity_after=total_equity,
                                target_weights=dict(weights),
                                trades_dollars=dict(trades),
                                fee_paid=fee_paid,
                                prices_at_rebalance={s: float(row[s]) for s in symbols},
                            )
                        )

        equity_curve_list.append((date, total_equity))
        asset_curve_rows.append((date, dict(positions_dollars)))

    equity_curve = pd.Series(
        {d: v for d, v in equity_curve_list},
        name="equity",
    ).sort_index()
    asset_curves = None
    if asset_curve_rows:
        dates_index = [d for d, _ in asset_curve_rows]
        asset_curves = pd.DataFrame(
            [v for _, v in asset_curve_rows],
            index=dates_index,
        ).sort_index()
        asset_curves.index.name = "date"
    metrics = compute_metrics(equity_curve)
    return BacktestResult(
        equity_curve=equity_curve,
        metrics=metrics,
        rebalance_decisions=decisions,
        asset_curves=asset_curves,
    )
