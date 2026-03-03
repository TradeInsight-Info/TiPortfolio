"""Backtest engines: base, schedule-based (symbol fetch), and volatility-based."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

import pandas as pd

from tiportfolio.allocation import AllocationStrategy, FixRatio, validate_vix_regime_bounds
from tiportfolio.backtest import BacktestResult, run_backtest
from tiportfolio.calendar import Schedule, get_rebalance_dates
from tiportfolio.data import fetch_prices, fetch_volatility_index, normalize_prices
from tiportfolio.utils.constants import VOLATILITY_INDEX_SYMBOLS as VOLATILITY_SYMBOLS
from tiportfolio.utils.symbols import normalize_volatility_symbol


def _vix_series_from_prices(
    prices: dict[str, pd.DataFrame] | pd.DataFrame,
    volatility_symbol: str,
    trading_dates: pd.DatetimeIndex,
) -> pd.Series:
    """Extract volatility (close) series from prices and align to trading_dates.
    
    Args:
        prices: Either a dict of DataFrames or a single DataFrame containing VIX data
        volatility_symbol: Symbol name for VIX (used when prices is a dict)
        trading_dates: Trading dates to align the VIX series to
    """
    if isinstance(prices, dict):
        if volatility_symbol not in prices:
            raise ValueError(
                f"prices must contain volatility symbol {volatility_symbol!r} for vix_regime / vol-based run"
            )
        df = prices[volatility_symbol]
    else:
        df = prices
    
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
        risk_free_rate: float = 0.04,
    ) -> None:
        self.allocation = allocation
        self.rebalance = rebalance
        self.fee_per_share = fee_per_share
        self.initial_value = initial_value
        self.risk_free_rate = risk_free_rate

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
            risk_free_rate=self.risk_free_rate,
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
        prices_df: dict[str, pd.DataFrame] | None = None,
    ) -> BacktestResult:
        """Run backtest by fetching prices for the given symbols and date range.

        If prices_df is provided and non-empty, use it as prices and do not fetch.
        Otherwise start and end are required and data is fetched via Alpaca or Yahoo Finance.
        """
        if prices_df is not None and len(prices_df) > 0:
            return super().run(prices=prices_df, start=start, end=end)
        if start is None or end is None:
            raise ValueError("start and end are required when not passing prices_df")
        prices = fetch_prices(symbols, start=start, end=end)
        return super().run(prices=prices, start=start, end=end)


class VolatilityBasedEngine(BacktestEngine):
    """Engine for VIX-based rebalance (vix_regime) or combined trigger.

    run() takes symbols and start/end (or prices_df); requires volatility_symbol.
    For schedule vix_regime also requires target_vix, lower_bound, upper_bound.
    Fetches data (or uses prices_df), builds vix_series, and passes vix_at_date
    in context so VixRegimeAllocation can choose high vs low allocation.
    """

    def run(
        self,
        symbols: Iterable[str],
        *,
        start: str | pd.Timestamp | None = None,
        end: str | pd.Timestamp | None = None,
        prices_df: dict[str, pd.DataFrame] | None = None,
        vix_df: pd.DataFrame | None = None,
        volatility_symbol: str = "",
        target_vix: float | None = None,
        lower_bound: float | None = None,
        upper_bound: float | None = None,
        rebalance_filter: Callable[
            [pd.Timestamp, pd.Series, pd.Timestamp | None], bool
        ] | None = None,
    ) -> BacktestResult:
        """Run backtest by fetching prices (or using prices_df); volatility_symbol required.

        If prices_df is provided and non-empty, use it as prices and do not fetch.
        If vix_df is provided, use it as the VIX data source instead of extracting from prices_df.
        Otherwise start and end are required and data is fetched (with volatility_symbol
        added to the symbol list if needed). For vix_regime, either vix_df or prices_df
        must contain the volatility symbol.
        """
        if prices_df is not None and len(prices_df) > 0:
            prices = prices_df
        else:
            if start is None or end is None:
                raise ValueError("start and end are required when not passing prices_df")
            vol_sym = normalize_volatility_symbol(volatility_symbol) if volatility_symbol else "VIX"
            sym_list = [s.upper() if isinstance(s, str) else str(s).upper() for s in symbols]
            # Fetch allocation symbols and volatility index separately; use fetch_volatility_index for the index
            prices = fetch_prices(sym_list, start=start, end=end)
            vol_df = fetch_volatility_index(vol_sym, start=start, end=end)
            prices[vol_sym] = vol_df

        vol_sym = normalize_volatility_symbol(volatility_symbol) if volatility_symbol else "VIX"
        if not vol_sym:
            raise ValueError("volatility_symbol is required for VolatilityBasedEngine.run()")
        allocation_keys = set(self.allocation.get_symbols())
        missing = allocation_keys - set(prices.keys())
        if missing:
            raise ValueError(
                f"prices missing keys for allocation: {sorted(missing)}"
            )
        
        prices_df = normalize_prices(
            {k: prices[k] for k in allocation_keys}, allocation_keys
        )
        trading_dates = prices_df.index
        
        # Handle VIX data extraction - prioritize vix_df if provided
        if vix_df is not None:
            vix_series = _vix_series_from_prices(vix_df, vol_sym, trading_dates)
        else:
            # Fetch VIX data using fetch_volatility_index when not provided
            try:
                vix_data = fetch_volatility_index(vol_sym, start=start, end=end)
                vix_series = _vix_series_from_prices(vix_data, vol_sym, trading_dates)
            except Exception as e:
                # Fallback to checking prices dict for backward compatibility
                if vol_sym in prices:
                    vix_series = _vix_series_from_prices(prices, vol_sym, trading_dates)
                else:
                    raise ValueError(
                        f"Failed to fetch VIX data for {vol_sym!r} and not found in prices. "
                        f"Error: {e}. Provide vix_df parameter or ensure VIX symbol is in prices."
                    )

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

        # Handle rebalance_filter logic by wrapping the allocation strategy
        if rebalance_filter is not None and vix_series is not None and self.rebalance.spec != "vix_regime":
            # Create a wrapper that handles the rebalance filter logic
            original_get_target_weights = allocation_strategy.get_target_weights
            
            def filtered_get_target_weights(date, total_equity, positions_dollars, prices, **kwargs):
                # Check if we should rebalance on this date
                if date in trading_dates:  # Only check on trading days
                    # Get last rebalance date from context or use a simple approach
                    last_rebalance_date = kwargs.get('last_rebalance_date')
                    should_rebalance = rebalance_filter(date, vix_series, last_rebalance_date)
                    if not should_rebalance:
                        # Return current positions (no rebalance)
                        return {sym: positions_dollars.get(sym, 0) / total_equity for sym in allocation_strategy.get_symbols()}
                return original_get_target_weights(date, total_equity, positions_dollars, prices, **kwargs)
            
            allocation_strategy.get_target_weights = filtered_get_target_weights

        # Handle vix_regime context_for_date logic by wrapping the allocation strategy
        allocation_strategy = self.allocation
        rebalance_dates_for_backtest = None
        
        if self.rebalance.spec == "vix_regime":
            # Calculate rebalance dates for vix_regime
            rebalance_dates_for_backtest = get_rebalance_dates(
                trading_dates,
                "vix_regime",
                start=start,
                end=end,
                vix_series=vix_series,
                target_vix=target_vix,
                lower_bound=lower_bound,
                upper_bound=upper_bound
            )
            
            original_get_target_weights = allocation_strategy.get_target_weights
            
            def context_aware_get_target_weights(date, total_equity, positions_dollars, prices, **kwargs):
                # Add VIX context for vix_regime
                context = context_for_date(date)
                kwargs.update(context)
                return original_get_target_weights(date, total_equity, positions_dollars, prices, **kwargs)
            
            allocation_strategy.get_target_weights = context_aware_get_target_weights

        return run_backtest(
            prices_df,
            allocation_strategy,
            self.rebalance.spec,
            self.fee_per_share,
            start=start,
            end=end,
            initial_value=self.initial_value,
            rebalance_dates=rebalance_dates_for_backtest,
            risk_free_rate=self.risk_free_rate,
        )
