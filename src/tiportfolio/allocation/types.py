from typing import TypeVar, TypedDict, Optional, List, Union, Callable, TypeAlias

from pandas import DataFrame



class StrategyData(TypedDict):
    prices: DataFrame  # DataFrame with price data, with columns['open', 'high', 'low', 'close', 'volume']
    other_datas: Optional[List[DataFrame]]  # DataFrame with other data, e.g. indicators


StrategyDataTypeVar = TypeVar('StrategyDataTypeVar', DataFrame, List[DataFrame])


StrategyType: TypeAlias = Callable[
    [StrategyData], Union[1, -1, 0]]  # A strategy function that returns 1 (long), -1 (short), or 0 (hold)
