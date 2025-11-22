from __future__ import annotations

from typing import Callable, Iterable, List, Sequence, Union, Optional, Dict, Any

import numpy as np
import pandas as pd

from ..helpers.common import DataCol, to_seconds


AlgoFn = Callable[[pd.DataFrame], pd.Series]


def _infer_close_col(df: pd.DataFrame) -> str:
    """Infer the close/price column name from a dataframe.

    Prioritizes the library's default column name, then common alternatives.
    """
    candidates = {
        DataCol.CLOSE.value,
        "Close",
        "close",
        "adj_close",
        "Adj Close",
        "adj close",
        "price",
        "last",
    }
    for col in df.columns:
        if str(col) in candidates:
            return str(col)
    # Fallback: choose the last numeric column if no standard name is present
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if not numeric_cols:
        raise ValueError("Could not find a price/close column in DataFrame.")
    return str(numeric_cols[-1])


def _bars_per_year(timeframe: str) -> float:
    """Approximate number of bars per year based on timeframe string.

    Uses seconds conversion when possible, falling back to common trading
    calendar assumptions for day/week/month bars.
    """
    tf = timeframe.lower().strip()
    # Special-case common calendar bars for financial data
    if tf.endswith("d") and tf[:-1].isdigit():
        # Approximate trading days in a year
        n = int(tf[:-1])
        return 252 / n
    if tf in ("1w", "1wk", "1week", "week", "weekly"):
        return 52.0
    if tf in ("1mo", "1mth", "1month", "month", "monthly"):
        return 12.0

    try:
        secs = to_seconds(tf)
        if secs <= 0:
            raise ValueError
        return (365 * 24 * 60 * 60) / secs
    except Exception:
        # Reasonable default: daily bars
        return 252.0


def _max_drawdown(equity_curve: pd.Series) -> float:
    """Compute maximum drawdown from an equity curve series."""
    if equity_curve.empty:
        return 0.0
    running_max = equity_curve.cummax()
    dd = (equity_curve / running_max) - 1.0
    return float(dd.min())


def _ensure_algo_list(algos: Union[AlgoFn, Sequence[AlgoFn]], n: int) -> List[AlgoFn]:
    if callable(algos):
        return [algos] * n
    algos_list = list(algos)
    if len(algos_list) != n:
        raise ValueError(
            f"Number of algorithms ({len(algos_list)}) must match number of datasets ({n})."
        )
    for i, a in enumerate(algos_list):
        if not callable(a):
            raise TypeError(f"Algorithm at index {i} is not callable.")
    return algos_list  # type: ignore[return-value]


def backtest(
    pairs: Sequence[tuple[str, pd.DataFrame, AlgoFn]],
    weight_adjust_fn: Optional[Callable[..., Union[pd.DataFrame, pd.Series]]] = None,
    timeframe: str = "1d",
    risk_free_annual: float = 0.0,
) -> Dict[str, Any]:
    """Run a simple vectorized backtest over multiple assets.

    Args:
        pairs: Sequence of tuples (symbol, dataframe, algorithm).
            - symbol: unique string identifier for the asset.
            - dataframe: indexed by datetime-like index and contains a price/close column.
            - algorithm: callable that accepts the asset DataFrame and returns a position
              series of the same index with exposure values (e.g., -1..+1). -1 means short,
              +1 means long, 0 means cash/flat.
        weight_adjust_fn: Optional callable to compute per-timestamp portfolio
            weights from positions.
            It will receive a list of tuples: (symbol, prices_df, positions_df),
            where prices_df and positions_df are single-column DataFrames aligned by
            time index for that symbol. It must return either a DataFrame of the same
            shape (weights per asset per timestamp, columns as symbols) or a Series of
            uniform weights per timestamp that will be broadcast to all assets.
            If None, defaults to equal weights among active (non-zero) positions each timestamp;
            if all positions are 0, it falls back to equal weights across all assets.
        timeframe: Bar timeframe string (e.g., '1d', '1h', '15m'). Used for annualizing metrics.
        risk_free_annual: Annual risk-free rate (as decimal) used in metrics calculation.

    Returns:
        Dict with keys: 'total_return', 'max_drawdown', 'volatility', 'sharpe', and additional
        helpful series under 'equity_curve' and 'portfolio_returns'.
    """
    if not isinstance(pairs, (list, tuple)) or len(pairs) == 0:
        raise ValueError("pairs must be a non-empty sequence of (symbol, DataFrame, algo) tuples.")

    # Validate symbols uniqueness and prepare per-asset aligned returns and positions
    symbols: List[str] = []
    asset_returns: List[pd.Series] = []
    asset_positions: List[pd.Series] = []
    asset_prices: List[pd.Series] = []

    seen = set()

    for i, pair in enumerate(pairs):
        try:
            symbol, df, algo = pair
        except Exception as e:
            raise TypeError(f"pairs[{i}] must be a tuple (symbol:str, DataFrame, algo)") from e

        if not isinstance(symbol, str) or not symbol:
            raise TypeError(f"pairs[{i}][0] must be a non-empty string symbol.")
        if symbol in seen:
            raise ValueError(f"Duplicate symbol in pairs: {symbol}")
        seen.add(symbol)
        symbols.append(symbol)

        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"pairs[{i}][1] is not a pandas DataFrame.")
        if not callable(algo):
            raise TypeError(f"pairs[{i}][2] is not callable (algorithm function).")
        if df.empty:
            raise ValueError(f"pairs[{i}][1] is an empty DataFrame.")

        # Ensure index is datetime-like for time alignment
        if not isinstance(df.index, (pd.DatetimeIndex, pd.PeriodIndex)):
            # Try to coerce an existing 'date' column to index
            if DataCol.DATE.value in df.columns:
                df = df.copy()
                df.index = pd.to_datetime(df[DataCol.DATE.value])
            else:
                # fallback: try to convert current index
                try:
                    df = df.copy()
                    df.index = pd.to_datetime(df.index)
                except Exception as e:
                    raise TypeError(
                        f"pairs[{i}][1] must have a datetime-like index or a 'date' column"
                    ) from e

        close_col = _infer_close_col(df)
        px = df[close_col].astype(float).rename(symbol)
        ret = px.pct_change().rename(symbol)

        pos = algo(df)
        if not isinstance(pos, pd.Series):
            raise TypeError(
                f"Algorithm for symbol {symbol!r} must return a pandas Series of positions indexed like the DataFrame."
            )
        # Align to df index, fill missing with 0 (flat), and shift to avoid lookahead
        pos = pos.reindex(df.index).fillna(0.0).astype(float).rename(symbol)
        pos = pos.shift(1)

        asset_returns.append(ret)
        asset_positions.append(pos)
        asset_prices.append(px)

    # Align all assets on a common timeline
    returns_df = pd.concat(asset_returns, axis=1).fillna(0.0)
    positions_df = pd.concat(asset_positions, axis=1).fillna(0.0)
    prices_df = pd.concat(asset_prices, axis=1).reindex_like(returns_df)

    # Strategy per-asset returns (pre-weights)
    strat_asset_rets = positions_df.values * returns_df.values
    strat_asset_rets = pd.DataFrame(
        strat_asset_rets, index=returns_df.index, columns=symbols
    )

    if strat_asset_rets.shape[1] == 0:
        raise ValueError("No strategy returns computed.")

    # Compute weights
    if weight_adjust_fn is not None:
        # Build the list of tuples (symbol, prices_df_single, positions_df_single)
        tuples_for_weights: list[tuple[str, pd.DataFrame, pd.DataFrame]] = []
        for sym in symbols:
            tuples_for_weights.append(
                (
                    sym,
                    prices_df[[sym]].copy(),
                    positions_df[[sym]].copy(),
                )
            )
        weights = weight_adjust_fn(tuples_for_weights)

        if isinstance(weights, pd.Series):
            # Broadcast series to all assets
            weights = pd.concat([weights] * strat_asset_rets.shape[1], axis=1)
            weights.columns = strat_asset_rets.columns
        elif isinstance(weights, pd.DataFrame):
            # Reindex to align
            weights = weights.reindex_like(strat_asset_rets)
            # If columns are not correctly labeled, set to symbols in order
            if list(weights.columns) != symbols:
                try:
                    weights = weights[symbols]
                except Exception:
                    weights.columns = symbols
        else:
            raise TypeError("weight_adjust_fn must return a pandas DataFrame or Series.")
    else:
        # Default: equal weight among active positions per timestamp
        active = (positions_df != 0).astype(float)
        counts = active.sum(axis=1)
        # Avoid division by zero; if no active positions, fall back to equal across all assets
        default_weights = active.div(counts.replace(0, np.nan), axis=0).fillna(1.0 / strat_asset_rets.shape[1])
        weights = default_weights
    # Normalize to ensure weights per timestamp sum to 1 (if they are all zeros/NaN, fallback equal)
    row_sums = weights.abs().sum(axis=1)
    normalized_weights = weights.div(row_sums.replace(0, np.nan), axis=0)
    normalized_weights = normalized_weights.fillna(1.0 / strat_asset_rets.shape[1])

    # Portfolio returns: sum of weighted asset strategy returns each timestamp
    portfolio_returns = (normalized_weights.values * strat_asset_rets.values).sum(axis=1)
    portfolio_returns = pd.Series(portfolio_returns, index=strat_asset_rets.index, name="portfolio_ret")

    # Compute equity curve
    equity_curve = (1.0 + portfolio_returns.fillna(0.0)).cumprod()

    # Metrics
    bars_year = _bars_per_year(timeframe)

    total_return = float(equity_curve.iloc[-1] - 1.0) if not equity_curve.empty else 0.0

    # Volatility (annualized)
    ret_std = float(portfolio_returns.std(ddof=0)) if not portfolio_returns.empty else 0.0
    volatility = ret_std * np.sqrt(bars_year)

    # Sharpe ratio (annualized), subtract period risk-free
    if risk_free_annual != 0:
        rf_per_period = (1.0 + risk_free_annual) ** (1.0 / bars_year) - 1.0
    else:
        rf_per_period = 0.0
    excess_mean = float((portfolio_returns - rf_per_period).mean()) if not portfolio_returns.empty else 0.0
    sharpe = (excess_mean / ret_std * np.sqrt(bars_year)) if ret_std > 0 else np.nan

    max_dd = _max_drawdown(equity_curve)

    return {
        "total_return": total_return,
        "max_drawdown": max_dd,
        "volatility": float(volatility),
        "sharpe": float(sharpe) if np.isfinite(sharpe) else np.nan,
        "equity_curve": equity_curve,
        "portfolio_returns": portfolio_returns,
        "bars_per_year": float(bars_year),
    }
