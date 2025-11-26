from datetime import datetime, timedelta
from typing import TypeVar, TypedDict, Optional, List

from pandas import DataFrame


class BaseHistoryData(TypedDict):
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
    risk_free_rate: float


class PortfolioConfig(TypedDict):
    fees_config: FeesConfig
    initial_capital: float
    time_start: datetime
    time_end: datetime
    timeframe: timedelta
