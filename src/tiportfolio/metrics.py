"""Performance metrics from daily equity series: Sharpe, CAGR, max drawdown, MAR."""

from __future__ import annotations

import pandas as pd

_NAN_METRICS: dict[str, float] = {
    "sharpe_ratio": float("nan"),
    "cagr": float("nan"),
    "max_drawdown": float("nan"),
    "mar_ratio": float("nan"),
    "kelly_leverage": float("nan"),
}


def compute_metrics(
    equity: pd.Series,
    *,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> dict[str, float]:
    """Compute Sharpe, CAGR, max_drawdown, and MAR from a daily equity series.

    equity: series of portfolio value (e.g. index = date).
    risk_free_rate: annual risk-free rate for Sharpe (default 0).
    periods_per_year: trading days per year for annualization (default 252).
    """
    if equity.empty or len(equity) < 2:
        return dict(_NAN_METRICS)
    equity = equity.dropna().sort_index()
    if len(equity) < 2:
        return dict(_NAN_METRICS)
    returns = equity.pct_change().dropna()
    if returns.empty:
        return dict(_NAN_METRICS)

    # CAGR: (end/start)^(252/n_days) - 1
    n_days = (equity.index[-1] - equity.index[0]).days
    if n_days <= 0:
        cagr = 0.0
    else:
        total_return = equity.iloc[-1] / equity.iloc[0]
        years = n_days / 365.25
        cagr = (total_return ** (1 / years) - 1.0) if years > 0 else 0.0

    # Max drawdown: max(peak - trough) / peak over rolling peak
    cummax = equity.cummax()
    drawdown = (equity - cummax) / cummax
    max_drawdown = drawdown.min()
    if max_drawdown >= 0:
        max_drawdown_pct = 0.0
    else:
        max_drawdown_pct = abs(max_drawdown)

    # Sharpe: annualized excess return / annualized vol
    excess = returns - (risk_free_rate / periods_per_year)
    if excess.std() == 0 or pd.isna(excess.std()):
        sharpe_ratio = float("nan")
        kelly_leverage = float("nan")
    else:
        sharpe_ratio = (excess.mean() / excess.std()) * (periods_per_year ** 0.5)
        # Kelly leverage: annualized mean excess return / (annualized std dev)^2
        annualized_mean_excess = excess.mean() * periods_per_year
        annualized_std_dev = excess.std() * (periods_per_year ** 0.5)
        kelly_leverage = annualized_mean_excess / (annualized_std_dev ** 2) if annualized_std_dev != 0 else float("nan")

    # MAR: CAGR / max_drawdown (as in docs/thoughts.md)
    mar_ratio = cagr / max_drawdown_pct if max_drawdown_pct > 0 else float("nan")

    return {
        "sharpe_ratio": float(sharpe_ratio),
        "cagr": float(cagr),
        "max_drawdown": float(max_drawdown_pct),
        "mar_ratio": float(mar_ratio),
        "kelly_leverage": float(kelly_leverage),
    }
