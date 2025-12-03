from datetime import datetime, timedelta
from typing import TypeVar, TypedDict, Optional, List

from pandas import DataFrame
from enum import Enum


class TradingSignal(Enum):
    """Canonical trading signal used by all strategy_library.

    The enum encodes *intent* (long/short/flat/hold) rather than a concrete
    position size.  Strategy implementations and allocation logic should work
    with this enum directly instead of raw integers such as ``1``, ``0`` or
    ``-1``.
    """

    LONG = 1
    """Open or maintain a long position."""


    EXIT = 0
    """Exit to a flat position (no exposure)."""

    SHORT = -1
    """Open or maintain a short position."""


class BaseHistoryData(TypedDict, total=False):
    prices: DataFrame  # DataFrame with price data, with columns['date'. 'open', 'high', 'low', 'close', 'volume', 'vmap']


HistoryDataExtension = TypeVar('HistoryDataExtension', bound=BaseHistoryData)
"""
 Data for strategy and portfolio has to extend BaseHistoryData
 We used TypeVar with bound to enforce that it has at least prices: DataFrame
"""


class StrategyData(TypedDict):
    prices: DataFrame  # DataFrame with price data, with columns['open', 'high', 'low', 'close', 'volume']
    other_datas: Optional[List[DataFrame]]  # DataFrame with other data, e.g. indicators


class FeesConfig(TypedDict):
    commission: float
    slippage: float




