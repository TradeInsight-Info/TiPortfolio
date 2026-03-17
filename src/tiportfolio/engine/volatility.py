"""Volatility-based backtest engine."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

import pandas as pd

from tiportfolio.allocation import validate_vix_regime_bounds
from tiportfolio.backtest import BacktestResult, run_backtest
from tiportfolio.calendar import get_rebalance_dates, normalize_price_index
from tiportfolio.data import fetch_prices, fetch_volatility_index, normalize_prices
from tiportfolio.engine.base import BacktestEngine
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

    date_index = pd.to_datetime(df.index).date
    trading_dates_normalized = pd.to_datetime(trading_dates).date

    raw = df["close"] if "close" in df.columns else df.iloc[:, 0]
    ser = pd.Series(raw.values, index=date_index).reindex(trading_dates_normalized).ffill().bfill()
    ser.index = trading_dates
    return ser


class _AllocationWrapper:
    """Local wrapper that overrides get_target_weights without mutating the original allocation."""

    def __init__(self, wrapped: Any, get_target_weights_fn: Any) -> None:
        self._wrapped = wrapped
        self._get_target_weights_fn = get_target_weights_fn

    def get_symbols(self) -> list[str]:
        return self._wrapped.get_symbols()

    def get_target_weights(self, *args: Any, **kwargs: Any) -> dict[str, float]:
        return self._get_target_weights_fn(*args, **kwargs)


class VolatilityBasedEngine(BacktestEngine):
    """Engine for VIX-based rebalance (vix_regime) or combined trigger.

    run() takes symbols and start/end (or prices_df); requires volatility_symbol.
    For schedule vix_regime also requires target_vix, lower_bound, upper_bound.
    Fetches data (or uses prices_df), builds vix_series, and passes vix_at_date
    in context so VixRegimeAllocation can choose high vs low allocation.
    """

    def __init__(self, *, freezing_days: int = 0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.freezing_days = freezing_days

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
        tz: str = "UTC",
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
        vol_sym = normalize_volatility_symbol(volatility_symbol) if volatility_symbol else "VIX"
        if prices_df is not None and len(prices_df) > 0:
            prices = prices_df
        else:
            if start is None or end is None:
                raise ValueError("start and end are required when not passing prices_df")
            sym_list = [s.upper() if isinstance(s, str) else str(s).upper() for s in symbols]
            prices = fetch_prices(sym_list, start=start, end=end)
        if not vol_sym:
            raise ValueError("volatility_symbol is required for VolatilityBasedEngine.run()")
        allocation_keys = set(self.allocation.get_symbols())
        missing = allocation_keys - set(prices.keys())
        if missing:
            raise ValueError(f"prices missing keys for allocation: {sorted(missing)}")

        prices_df = normalize_prices(
            {k: prices[k] for k in allocation_keys}, allocation_keys
        )
        trading_dates = prices_df.index

        if vix_df is not None:
            vix_df = normalize_price_index(vix_df, tz=tz)
            vix_series = _vix_series_from_prices(vix_df, vol_sym, trading_dates)
        else:
            vix_data = fetch_volatility_index(vol_sym, start=start, end=end)
            vix_series = _vix_series_from_prices(vix_data, vol_sym, trading_dates)

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
                use_high_vol = False
                if vix_value is not None:
                    upper_thresh = target_vix + upper_bound
                    lower_thresh = target_vix + lower_bound
                    use_high_vol = vix_value >= upper_thresh
                return {
                    "vix_at_date": vix_value,
                    "use_high_vol_allocation": use_high_vol,
                }

        allocation_strategy = self.allocation
        rebalance_dates_for_backtest = None

        if rebalance_filter is not None and vix_series is not None and self.rebalance.spec != "vix_regime":
            _orig_weights = allocation_strategy.get_target_weights

            def filtered_get_target_weights(
                date: pd.Timestamp,
                total_equity: float,
                positions_dollars: dict[str, float],
                prices: pd.Series,
                **kwargs: Any,
            ) -> dict[str, float]:
                last_rebalance_date = kwargs.get("last_rebalance_date")
                filter_date = kwargs.get("signal_date", date)
                if not rebalance_filter(filter_date, vix_series, last_rebalance_date):
                    return {sym: positions_dollars.get(sym, 0) / total_equity for sym in allocation_strategy.get_symbols()}
                return _orig_weights(date, total_equity, positions_dollars, prices, **kwargs)

            allocation_strategy = _AllocationWrapper(allocation_strategy, filtered_get_target_weights)

        if self.rebalance.spec == "vix_regime":
            rebalance_dates_for_backtest = get_rebalance_dates(
                trading_dates,
                "vix_regime",
                start=start,
                end=end,
                vix_series=vix_series,
                target_vix=target_vix,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                signal_delay=self.signal_delay,
            )

            if self.freezing_days > 0:
                filtered_dates = []
                last_rebalance = None
                for date in sorted(rebalance_dates_for_backtest):
                    if last_rebalance is None or (date - last_rebalance).days > self.freezing_days:
                        filtered_dates.append(date)
                        last_rebalance = date
                rebalance_dates_for_backtest = pd.DatetimeIndex(filtered_dates)

            _orig_weights = allocation_strategy.get_target_weights

            def context_aware_get_target_weights(
                date: pd.Timestamp,
                total_equity: float,
                positions_dollars: dict[str, float],
                prices: pd.Series,
                **kwargs: Any,
            ) -> dict[str, float]:
                context_date = kwargs.get("signal_date", date)
                context = context_for_date(context_date)
                kwargs.update(context)
                return _orig_weights(date, total_equity, positions_dollars, prices, **kwargs)

            allocation_strategy = _AllocationWrapper(allocation_strategy, context_aware_get_target_weights)

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
            signal_delay=self.signal_delay,
        )
