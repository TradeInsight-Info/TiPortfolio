from typing import Optional, Dict
import numpy as np


def calculate_portfolio_metrics(
    values: np.ndarray,
    initial_capital: float,
    period_returns: Optional[np.ndarray] = None,
    risk_free_rate: Optional[float] = None,
    num_trading_days: Optional[int] = None,
    calculate_sharpe: bool = True,
    calculate_annualized: bool = True,
) -> Dict[str, float]:
    """
    Calculate portfolio performance metrics from a series of portfolio values.

    Args:
        values: Array of portfolio values over time
        initial_capital: Initial capital invested
        period_returns: Optional array of period returns. If not provided,
            will be calculated from values.
        risk_free_rate: Optional risk-free rate for Sharpe ratio calculation
        num_trading_days: Optional number of trading days for annualized return
        calculate_sharpe: Whether to calculate Sharpe ratio (default True)
        calculate_annualized: Whether to calculate annualized return (default True)

    Returns:
        Dictionary containing final_value, total_return, max_drawdown,
        mar_ratio, sharpe_ratio, and annualized_return.
    """
    if len(values) < 2:
        raise ValueError(
            "Insufficient data to calculate metrics. Need at least 2 time steps."
        )

    # Convert to numpy array if needed and ensure it's clean
    values = np.array(values)
    values_clean = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)

    # Calculate period returns if not provided
    if period_returns is None:
        denominator = values_clean[:-1].copy()
        denominator[denominator == 0] = 1e-10
        period_returns = np.diff(values_clean) / denominator
        period_returns = np.nan_to_num(period_returns, nan=0.0, posinf=0.0, neginf=0.0)
    else:
        # Ensure period_returns is clean
        period_returns = np.array(period_returns)
        period_returns = np.nan_to_num(period_returns, nan=0.0, posinf=0.0, neginf=0.0)

    # Calculate cumulative returns
    final_value = float(values_clean[-1])
    total_return = (final_value - initial_capital) / initial_capital

    # Calculate drawdowns with protection against division by zero and NaN
    cumulative_max = np.maximum.accumulate(values_clean)
    cumulative_max = np.where(cumulative_max == 0, 1e-10, cumulative_max)
    drawdowns = (values_clean / cumulative_max) - 1.0
    drawdowns = np.nan_to_num(drawdowns, nan=0.0, posinf=0.0, neginf=0.0)
    max_drawdown = float(np.min(drawdowns))

    # Calculate annualized return
    if calculate_annualized and num_trading_days is not None:
        if num_trading_days > 0:
            years = num_trading_days / 252.0
            if years > 0:
                annualized_return = (1.0 + total_return) ** (1.0 / years) - 1.0
            else:
                annualized_return = 0.0
        else:
            annualized_return = 0.0
    else:
        annualized_return = 0.0

    # Calculate Sharpe ratio with protection against invalid values
    if calculate_sharpe and risk_free_rate is not None:
        if len(period_returns) > 1:
            valid_returns = period_returns[np.isfinite(period_returns)]
            if len(valid_returns) > 1:
                annualized_volatility = np.std(valid_returns, ddof=1) * np.sqrt(252.0)
                if annualized_volatility > 1e-10 and np.isfinite(annualized_volatility):
                    sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility
                    if not np.isfinite(sharpe_ratio):
                        sharpe_ratio = 0.0
                else:
                    sharpe_ratio = 0.0
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
    else:
        sharpe_ratio = 0.0

    # Calculate MAR ratio (return divided by max drawdown)
    max_dd_abs = abs(max_drawdown)
    if max_dd_abs > 1e-10:
        mar_ratio = total_return / max_dd_abs
    else:
        mar_ratio = 0.0

    return {
        "final_value": final_value,
        "total_return": total_return,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe_ratio,
        "annualized_return": annualized_return,
        "mar_ratio": mar_ratio,
    }

