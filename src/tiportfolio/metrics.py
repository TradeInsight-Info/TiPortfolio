"""Pure performance metrics computed from an equity curve.

Every function here is a pure function of an equity-curve ``Series`` and a
:class:`TiConfig`: no plotting, no I/O, no run metadata. This is the test
surface for the return/risk maths — feed a synthetic Series and assert.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from tiportfolio.config import TiConfig


def return_stats(eq: pd.Series, config: TiConfig) -> dict[str, float]:
    """Headline return/risk statistics (Sharpe, Sortino, CAGR, drawdown, ...).

    Returns raw (unrounded) values keyed in display order.
    """
    bars_per_year = config.bars_per_year
    rf_per_bar = config.risk_free_rate / bars_per_year

    total_return = (eq.iloc[-1] / eq.iloc[0]) - 1.0

    # CAGR
    n_bars = len(eq)
    years = n_bars / bars_per_year
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1.0 if years > 0 else 0.0

    # Max drawdown
    cummax = eq.cummax()
    drawdown = (eq - cummax) / cummax
    max_dd = drawdown.min()

    # Daily returns and excess
    returns = eq.pct_change().dropna()
    excess = returns - rf_per_bar

    # Annualised Sharpe ratio
    sharpe = (
        float(excess.mean()) / float(excess.std()) * math.sqrt(bars_per_year)
        if float(excess.std()) > 0
        else 0.0
    )

    # Annualised Sortino ratio (downside deviation only)
    downside = excess[excess < 0]
    downside_std = float(downside.std()) if len(downside) > 0 else 0.0
    sortino = (
        float(excess.mean()) / downside_std * math.sqrt(bars_per_year)
        if downside_std > 0
        else 0.0
    )

    # Calmar ratio (CAGR / |max_drawdown|)
    calmar = abs(cagr / max_dd) if max_dd != 0 else 0.0

    # Kelly leverage (mean_excess / var_excess)
    excess_var = float(excess.var())
    kelly = float(excess.mean()) / excess_var if excess_var > 0 else 0.0

    return {
        "sharpe": sharpe,
        "calmar": calmar,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "cagr": cagr,
        "risk_free_rate": config.risk_free_rate,
        "total_return": total_return,
        "kelly": kelly,
        "final_value": float(eq.iloc[-1]),
    }


def period_returns(eq: pd.Series, config: TiConfig) -> dict[str, Any]:
    """Trailing period returns from the equity curve."""
    last_date = eq.index[-1]
    bars_per_year = config.bars_per_year

    def _ret(start_date: pd.Timestamp) -> float:
        """Simple return from start_date to last equity value."""
        idx = eq.index.searchsorted(start_date)
        if idx >= len(eq):
            return float("nan")
        return float(eq.iloc[-1] / eq.iloc[idx] - 1.0)

    def _ann_ret(start_date: pd.Timestamp, years: float) -> float:
        """Annualised return from start_date."""
        idx = eq.index.searchsorted(start_date)
        if idx >= len(eq):
            return float("nan")
        ratio = eq.iloc[-1] / eq.iloc[idx]
        return float(ratio ** (1.0 / years) - 1.0)

    first_date = eq.index[0]
    total_years = len(eq) / bars_per_year

    # Month-to-date: start of current month
    mtd_start = last_date.replace(day=1)
    # Year-to-date: start of current year
    ytd_start = last_date.replace(month=1, day=1)

    # Lookback dates
    m3_start = last_date - pd.DateOffset(months=3)
    m6_start = last_date - pd.DateOffset(months=6)
    y1_start = last_date - pd.DateOffset(years=1)
    y3_start = last_date - pd.DateOffset(years=3)
    y5_start = last_date - pd.DateOffset(years=5)
    y10_start = last_date - pd.DateOffset(years=10)

    return {
        "mtd": _ret(mtd_start),
        "3m": _ret(m3_start),
        "6m": _ret(m6_start),
        "ytd": _ret(ytd_start),
        "1y": _ret(y1_start),
        "3y_ann": _ann_ret(y3_start, 3.0) if y3_start >= first_date else float("nan"),
        "5y_ann": _ann_ret(y5_start, 5.0) if y5_start >= first_date else float("nan"),
        "10y_ann": _ann_ret(y10_start, 10.0) if y10_start >= first_date else float("nan"),
        "incep_ann": float(
            (eq.iloc[-1] / eq.iloc[0]) ** (1.0 / total_years) - 1.0
        ) if total_years > 0 else 0.0,
    }


def daily_stats(eq: pd.Series, config: TiConfig) -> dict[str, float]:
    """Daily return statistics."""
    bars_per_year = config.bars_per_year
    daily = eq.pct_change().dropna()

    return {
        "daily_mean_ann": float(daily.mean() * bars_per_year),
        "daily_vol_ann": float(daily.std() * math.sqrt(bars_per_year)),
        "daily_skew": float(daily.skew()),
        "daily_kurt": float(daily.kurt()),
        "best_day": float(daily.max()),
        "worst_day": float(daily.min()),
    }


def monthly_stats(eq: pd.Series, config: TiConfig) -> dict[str, float]:
    """Monthly return statistics."""
    rf = config.risk_free_rate
    monthly = eq.resample("ME").last().pct_change().dropna()

    if len(monthly) < 2:
        return {
            "monthly_sharpe": 0.0, "monthly_sortino": 0.0,
            "monthly_mean_ann": 0.0, "monthly_vol_ann": 0.0,
            "monthly_skew": 0.0, "monthly_kurt": 0.0,
            "best_month": float(monthly.max()) if len(monthly) > 0 else 0.0,
            "worst_month": float(monthly.min()) if len(monthly) > 0 else 0.0,
        }

    rf_monthly = rf / 12.0
    excess = monthly - rf_monthly
    std = float(excess.std())
    downside = excess[excess < 0]
    down_std = float(downside.std()) if len(downside) > 0 else 0.0

    return {
        "monthly_sharpe": float(excess.mean()) / std * math.sqrt(12) if std > 0 else 0.0,
        "monthly_sortino": float(excess.mean()) / down_std * math.sqrt(12) if down_std > 0 else 0.0,
        "monthly_mean_ann": float(monthly.mean() * 12),
        "monthly_vol_ann": float(monthly.std() * math.sqrt(12)),
        "monthly_skew": float(monthly.skew()),
        "monthly_kurt": float(monthly.kurt()),
        "best_month": float(monthly.max()),
        "worst_month": float(monthly.min()),
    }


def yearly_stats(eq: pd.Series, config: TiConfig) -> dict[str, float]:
    """Yearly return statistics."""
    rf = config.risk_free_rate
    yearly = eq.resample("YE").last().pct_change().dropna()

    if len(yearly) < 2:
        return {
            "yearly_sharpe": 0.0, "yearly_sortino": 0.0,
            "yearly_mean": float(yearly.mean()) if len(yearly) > 0 else 0.0,
            "yearly_vol": 0.0,
            "yearly_skew": 0.0, "yearly_kurt": 0.0,
            "best_year": float(yearly.max()) if len(yearly) > 0 else 0.0,
            "worst_year": float(yearly.min()) if len(yearly) > 0 else 0.0,
        }

    excess = yearly - rf
    std = float(excess.std())
    downside = excess[excess < 0]
    down_std = float(downside.std()) if len(downside) > 0 else 0.0

    return {
        "yearly_sharpe": float(excess.mean()) / std if std > 0 else 0.0,
        "yearly_sortino": float(excess.mean()) / down_std if down_std > 0 else 0.0,
        "yearly_mean": float(yearly.mean()),
        "yearly_vol": float(yearly.std()),
        "yearly_skew": float(yearly.skew()),
        "yearly_kurt": float(yearly.kurt()),
        "best_year": float(yearly.max()),
        "worst_year": float(yearly.min()),
    }


def drawdown_analysis(eq: pd.Series, config: TiConfig) -> dict[str, float]:
    """Drawdown episode analysis and win-rate metrics."""
    cummax = eq.cummax()
    drawdown = (eq - cummax) / cummax

    # Identify drawdown episodes (contiguous periods below cummax)
    in_dd = eq < cummax
    episodes: list[dict[str, Any]] = []
    current_start = None
    current_trough = 0.0

    for i, is_dd in enumerate(in_dd):
        if is_dd:
            if current_start is None:
                current_start = i
                current_trough = float(drawdown.iloc[i])
            else:
                current_trough = min(current_trough, float(drawdown.iloc[i]))
        else:
            if current_start is not None:
                start_dt = eq.index[current_start]
                end_dt = eq.index[i]
                days = (end_dt - start_dt).days
                episodes.append({"trough": current_trough, "days": days})
                current_start = None
                current_trough = 0.0

    # Handle ongoing drawdown at end of series
    if current_start is not None:
        start_dt = eq.index[current_start]
        end_dt = eq.index[-1]
        days = (end_dt - start_dt).days
        episodes.append({"trough": current_trough, "days": days})

    avg_dd = float(np.mean([e["trough"] for e in episodes])) if episodes else 0.0
    avg_dd_days = float(np.mean([e["days"] for e in episodes])) if episodes else 0.0

    # Monthly return analysis
    monthly = eq.resample("ME").last().pct_change().dropna()
    up = monthly[monthly > 0]
    down = monthly[monthly < 0]
    avg_up_month = float(up.mean()) if len(up) > 0 else 0.0
    avg_down_month = float(down.mean()) if len(down) > 0 else 0.0

    # Win year %
    yearly = eq.resample("YE").last().pct_change().dropna()
    win_year_pct = float((yearly > 0).mean()) if len(yearly) > 0 else 0.0

    # Win 12-month rolling %
    if len(monthly) >= 13:
        rolling_12m = monthly.rolling(12).apply(
            lambda x: float(np.prod(1 + x) - 1), raw=True
        ).dropna()
        win_12m_pct = float((rolling_12m > 0).mean()) if len(rolling_12m) > 0 else 0.0
    else:
        win_12m_pct = 0.0

    return {
        "avg_drawdown": avg_dd,
        "avg_drawdown_days": avg_dd_days,
        "avg_up_month": avg_up_month,
        "avg_down_month": avg_down_month,
        "win_year_pct": win_year_pct,
        "win_12m_pct": win_12m_pct,
    }
