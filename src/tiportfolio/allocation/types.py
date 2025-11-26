from typing import TypeVar, TypedDict

from pandas import DataFrame


class BaseHistoryData(TypedDict):
    prices: DataFrame  # DataFrame with price data, with columns['open', 'high', 'low', 'close', 'volume']


HistoryDataExtension = TypeVar('HistoryDataExtension', bound=BaseHistoryData)
"""
 Data for strategy and allocation has to extend BaseHistoryData
 We used TypeVar with bound to enforce that it has at least prices: DataFrame
"""
