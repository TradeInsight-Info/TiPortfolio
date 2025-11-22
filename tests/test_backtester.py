import os
import sys

import numpy as np
import pandas as pd

# Ensure src is on path for direct test execution without installation
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from src.tiportfolio.backtester import backtest  # noqa: E402


def test_backtester_simple_increasing_prices():
    # Create a simple price series that increases each day
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = [100.0, 101.0, 102.0, 103.0]
    df = pd.DataFrame({"close": prices}, index=dates)

    # Simple algorithm: always long (1.0)
    def always_long(_df: pd.DataFrame) -> pd.Series:
        return pd.Series(1.0, index=_df.index)

    # pairs: list of (symbol, dataset, algorithm)
    pairs = [("TEST", df, always_long)]

    # Weight adjust function: equal weights across assets using new signature
    # Receives a list of tuples: (symbol, prices_df, positions_df)
    def weight_fn_equal_weight(pairs):
        symbols = [sym for sym, _prices, _positions in pairs]
        # Use index from the first positions_df (all are aligned by backtester)
        idx = pairs[0][2].index
        n = len(symbols)
        return pd.DataFrame(1.0 / n, index=idx, columns=symbols)

    # Call with explicit weight function to validate new API and symbol-based alignment
    res = backtest(pairs=pairs, weight_adjust_fn=weight_fn_equal_weight, timeframe="1d", risk_free_annual=0.0)

    # Expected total return: product of (1 + returns) minus 1
    # With position shift by 1 bar, we start capturing from the second row (day 2)
    r0 = (prices[1] - prices[0]) / prices[0]  # from day 1 to day 2
    r1 = (prices[2] - prices[1]) / prices[1]  # from day 2 to day 3
    r2 = (prices[3] - prices[2]) / prices[2]  # from day 3 to day 4
    expected_total_return = (1 + r0) * (1 + r1) * (1 + r2) - 1

    assert np.isclose(res["total_return"], expected_total_return, rtol=1e-6, atol=1e-12)

    # Strictly increasing equity curve -> no drawdown
    assert np.isclose(res["max_drawdown"], 0.0, atol=1e-12)

    # Volatility should be positive (non-zero returns present)
    assert res["volatility"] > 0

    # Sharpe should be positive (given positive average returns and zero risk-free)
    # Some implementations may be very small due to sample size; just ensure finite and >= 0
    assert np.isfinite(res["sharpe"]) and res["sharpe"] >= 0

    # Bars per year for 1d should be 252
    assert res["bars_per_year"] == 252.0

    # Sanity check: portfolio_returns length equals number of rows
    assert len(res["portfolio_returns"]) == len(df)
