"""Backtest engines: base, schedule-based (symbol fetch), and volatility-based."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

import pandas as pd

from tiportfolio.allocation import AllocationStrategy, FixRatio, validate_vix_regime_bounds
from tiportfolio.backtest import BacktestResult, run_backtest
from tiportfolio.calendar import Schedule
from tiportfolio.data import fetch_prices, fetch_volatility_index, normalize_prices, VOLATILITY_INDEX_SYMBOLS


VOLATILITY_SYMBOLS = VOLATILITY_INDEX_SYMBOLS


def _normalize_volatility_symbol(symbol: str) -> str:
    """Return symbol without ^ and uppercased; validate against VOLATILITY_SYMBOLS."""
    s = symbol.strip().upper().lstrip("^")
    if s not in VOLATILITY_SYMBOLS:
        raise ValueError(
            f"volatility_symbol must be one of {VOLATILITY_SYMBOLS}; got {symbol!r}"
        )
    return s


def _vix_series_from_prices(
    prices: dict[str, pd.DataFrame],
    volatility_symbol: str,
    trading_dates: pd.DatetimeIndex,
) -> pd.Series:
    """Extract volatility (close) series from prices and align to trading_dates."""
    if volatility_symbol not in prices:
        raise ValueError(
            f"prices must contain volatility symbol {volatility_symbol!r} for vix_regime / vol-based run"
        )
    df = prices[volatility_symbol]
    
    # Normalize dates by removing time component and timezone
    df.index = pd.to_datetime(df.index).date
    trading_dates_normalized = pd.to_datetime(trading_dates).date
    
    ser = df["close"] if "close" in df.columns else df.iloc[:, 0]
    ser = ser.reindex(trading_dates_normalized).ffill().bfill()
    ser.index = trading_dates  # Restore original trading_dates index
    return ser


class BacktestEngine:
    """Engine for running backtests with AllocationStrategy and scheduled rebalance."""

    def __init__(
        self,
        *,
        allocation: FixRatio | AllocationStrategy,
        rebalance: Schedule,
        fee_per_share: float = 0.0035,
        initial_value: float = 10000.0,
    ) -> None:
        self.allocation = allocation
        self.rebalance = rebalance
        self.fee_per_share = fee_per_share
        self.initial_value = initial_value

    def run(
        self,
        prices: dict[str, pd.DataFrame],
        *,
        start: str | pd.Timestamp | None = None,
        end: str | pd.Timestamp | None = None,
    ) -> BacktestResult:
        """Run backtest. prices: dict symbol -> DataFrame (date index, price column)."""
        allocation_keys = set(self.allocation.get_symbols())
        prices_df = normalize_prices(prices, allocation_keys)
        return run_backtest(
            prices_df,
            self.allocation,
            self.rebalance.spec,
            self.fee_per_share,
            start=start,
            end=end,
            initial_value=self.initial_value,
        )


class ScheduleBasedEngine(BacktestEngine):
    """Backtest engine that fetches price data by symbols (Alpaca or Yahoo Finance).

    Same constructor as BacktestEngine. run() takes symbols and start/end
    instead of prices; fetches data internally then runs the backtest.
    """

    def run(
        self,
        symbols: Iterable[str],
        *,
        start: str | pd.Timestamp | None = None,
        end: str | pd.Timestamp | None = None,
        dfs_in_dict: dict[str, pd.DataFrame] | None = None,
    ) -> BacktestResult:
        """Run backtest by fetching prices for the given symbols and date range.

        If dfs_in_dict is provided and non-empty, use it as prices and do not fetch.
        Otherwise start and end are required and data is fetched via Alpaca or Yahoo Finance.
        """
        if dfs_in_dict is not None and len(dfs_in_dict) > 0:
            return super().run(prices=dfs_in_dict, start=start, end=end)
        if start is None or end is None:
            raise ValueError("start and end are required when not passing dfs_in_dict")
        prices = fetch_prices(symbols, start=start, end=end)
        return super().run(prices=prices, start=start, end=end)


class VolatilityBasedEngine(BacktestEngine):
    """Engine for VIX-based rebalance (vix_regime) or combined trigger.

    run() takes symbols and start/end (or dfs_in_dict); requires volatility_symbol.
    For schedule vix_regime also requires target_vix, lower_bound, upper_bound.
    Fetches data (or uses dfs_in_dict), builds vix_series, and passes vix_at_date
    in context so VixRegimeAllocation can choose high vs low allocation.
    """

    def run(
        self,
        symbols: Iterable[str],
        *,
        start: str | pd.Timestamp | None = None,
        end: str | pd.Timestamp | None = None,
        dfs_in_dict: dict[str, pd.DataFrame] | None = None,
        volatility_symbol: str = "",
        target_vix: float | None = None,
        lower_bound: float | None = None,
        upper_bound: float | None = None,
        rebalance_filter: Callable[
            [pd.Timestamp, pd.Series, pd.Timestamp | None], bool
        ] | None = None,
    ) -> BacktestResult:
        """Run backtest by fetching prices (or using dfs_in_dict); volatility_symbol required.

        If dfs_in_dict is provided and non-empty, use it as prices and do not fetch.
        Otherwise start and end are required and data is fetched (with volatility_symbol
        added to the symbol list if needed). For vix_regime, dfs_in_dict must contain
        the volatility symbol.
        """
        if dfs_in_dict is not None and len(dfs_in_dict) > 0:
            prices = dfs_in_dict
        else:
            if start is None or end is None:
                raise ValueError("start and end are required when not passing dfs_in_dict")
            vol_sym = _normalize_volatility_symbol(volatility_symbol) if volatility_symbol else "VIX"
            sym_list = [s.upper() if isinstance(s, str) else str(s).upper() for s in symbols]
            # Fetch allocation symbols and volatility index separately; use fetch_volatility_index for the index
            prices = fetch_prices(sym_list, start=start, end=end)
            vol_df = fetch_volatility_index(vol_sym, start=start, end=end)
            prices[vol_sym] = vol_df

        vol_sym = _normalize_volatility_symbol(volatility_symbol) if volatility_symbol else "VIX"
        if not vol_sym:
            raise ValueError("volatility_symbol is required for VolatilityBasedEngine.run()")
        allocation_keys = set(self.allocation.get_symbols())
        missing = allocation_keys - set(prices.keys())
        if missing:
            raise ValueError(
                f"prices missing keys for allocation: {sorted(missing)}"
            )
        if vol_sym not in prices:
            raise ValueError(
                f"prices must contain volatility symbol {vol_sym!r} for VolatilityBasedEngine"
            )
        prices_df = normalize_prices(
            {k: prices[k] for k in allocation_keys}, allocation_keys
        )
        trading_dates = prices_df.index
        vix_series = _vix_series_from_prices(prices, vol_sym, trading_dates)

        schedule_kwargs: dict[str, Any] = {}
        context_for_date: Callable[[pd.Timestamp], dict[str, Any]] | None = None

        if self.rebalance.spec == "vix_regime":
            if target_vix is None or lower_bound is None or upper_bound is None:
                raise ValueError(
                    "schedule vix_regime requires target_vix, lower_bound, upper_bound"
                )
            validate_vix_regime_bounds(target_vix, lower_bound, upper_bound)
            schedule_kwargs = {
                "vix_series": vix_series,
                "target_vix": target_vix,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
            }
            vix_ser = vix_series

            def context_for_date(d: pd.Timestamp) -> dict[str, Any]:
                v = vix_ser.asof(d)
                vix_value = None if pd.isna(v) else float(v)
                
                # Calculate allocation decision in the engine
                use_high_vol = False
                if vix_value is not None:
                    upper_thresh = target_vix + upper_bound
                    lower_thresh = target_vix + lower_bound
                    use_high_vol = vix_value >= upper_thresh
                
                return {
                    "vix_at_date": vix_value,
                    "use_high_vol_allocation": use_high_vol
                }

            context_for_date = context_for_date

        return run_backtest(
            prices_df,
            self.allocation,
            self.rebalance.spec,
            self.fee_per_share,
            start=start,
            end=end,
            initial_value=self.initial_value,
            rebalance_filter=rebalance_filter,
            vix_series=vix_series if rebalance_filter else None,
            context_for_date=context_for_date,
            schedule_kwargs=schedule_kwargs or None,
        )
