from abc import ABC, abstractmethod
from typing import TypedDict, Optional, Tuple

from pandas import DataFrame, Timestamp, DatetimeIndex

from tiportfolio.portfolio.types import TradingSignal
from tiportfolio.utils.constants import BASIC_REQUIRED_COLUMNS


class TradingAlgorithmConfig(TypedDict, total=False):
    set_signal_back: bool  # True by default


class TradingAlgorithmStrategyResult(TypedDict):
    final_value: float
    total_return: float
    max_drawdown: float
    mar_ratio: float


class Trading(ABC):

    def __init__(self,
                 strategy_name: str,
                 stock_symbol: str, *,
                 prices: DataFrame,
                 config: TradingAlgorithmConfig = None,
                 **other_data: DataFrame,
                 ) -> None:
        self.strategy_name = strategy_name
        self.symbol_stock = stock_symbol
        self.set_signal_back = config.get('set_signal_back', True)
        for col in BASIC_REQUIRED_COLUMNS:
            if col not in prices.columns:
                raise ValueError(f"Data['prices'] must have '{col}' column")

        self.prices: DataFrame = prices

        if self.prices.empty:
            raise ValueError("Data['prices'] is empty")

        if 'date' not in self.prices.columns and 'datetime' in self.prices.columns:
            self.prices.rename(columns={'datetime': 'date'}, inplace=True)

        if self.prices.index.name != 'date' and 'date' in self.prices.columns:
            self.prices.set_index('date', inplace=True)

        if self.prices.index.name != 'date' or not isinstance(self.prices.index, DatetimeIndex):
            raise ValueError("Data['prices'] index must be named 'date' and be of type DatetimeIndex")

        self.before_all()

    def __str__(self) -> str:
        return f"{self.strategy_name} - {self.symbol_stock}"

    def __hash__(self) -> int:
        return hash(self.__str__())

    @property
    def name(self) -> str:
        return self.__str__()

    @property
    def dataframe(self) -> DataFrame:
        return self.prices

    @property
    def all_steps(self) -> DatetimeIndex:
        return self.prices.index

    def set_signal_back_to_prices_df_on_step(self, step: Timestamp, signal: TradingSignal) -> None:
        """
        Post run actions after each _get_signal step is complete
        We can update the column 'signal' in the prices DataFrame here
        :return: None
        """
        self.prices.loc[step, 'signal'] = signal.value

    def execute(self, step: Timestamp) -> TradingSignal:
        """
        Generate trading signals using the strategy function
        :param step: datetime
        :return: TradingSignal
        """
        idx = self.prices.index.get_loc(step)
        if isinstance(idx, slice):
            idx = idx.stop - 1
        history = self.prices.iloc[:idx]
        signal = self.run_at_step(history, step)
        if self.set_signal_back:
            self.set_signal_back_to_prices_df_on_step(step, signal)
        return signal

    def before_all(self) -> None:
        """
        Prepare History Data for Analysis
        Update the data in place for example, adding indicators as a new columns to the prices DataFrame
        Be careful, avoid look-ahead bias
        :return: None
        """
        pass

    @abstractmethod
    def run_at_step(self, history_prices: DataFrame, step: Timestamp) -> TradingSignal:
        """
        Analyse History Data and Predict Next Signal (Current Time)
        :param step:
        :param history_prices:
        :return: TradingSignal
        """
        raise NotImplementedError("_analyse_next_signal method must be implemented by subclass")

    def after_all(self) -> Optional[Tuple[DataFrame, TradingAlgorithmStrategyResult]]:
        """Compute basic performance statistics after a backtest run.

        The implementation assumes that ``execute`` has been called for
        each timestamp in ``prices_df.index`` and that, when
        ``self._set_signal_back`` is ``True``, a numeric ``signal`` column
        is present in ``prices_df`` containing the integer values of the
        :class:`TradingSignal` enum (e.g. 1 for long, 0 for exit, -1 for
        short).

        It returns a *view* of the last 100 rows of the prices DataFrame
        (including the newly-added performance columns) together with a
        small dictionary of summary statistics.
        """

        if "signal" not in self.dataframe.columns:
            # Nothing to evaluate – the strategy never populated signals.
            print(f"No signals were recorded in prices DataFrame for {self.symbol_stock}.")
            return None

        returns = self.dataframe["close"].pct_change(fill_method=None)

        shifted_signal = self.dataframe["signal"].shift(1).fillna(0)

        self.dataframe["pnl"] = (shifted_signal * returns).fillna(0)
        self.dataframe["value"] = (1 + self.dataframe["pnl"]).cumprod()
        self.dataframe["cumulative_pnl"] = self.dataframe["value"] - 1

        self.dataframe["cumulative_max"] = self.dataframe["value"].cummax()
        self.dataframe["drawdown"] = self.dataframe["value"] / self.dataframe["cumulative_max"] - 1
        self.dataframe["max_drawdown"] = self.dataframe["drawdown"].cummin()

        max_dd_abs = self.dataframe["max_drawdown"].abs().replace(0, 1e-10)
        self.dataframe["mar_ratio"] = self.dataframe["cumulative_pnl"] / max_dd_abs

        summary: TradingAlgorithmStrategyResult = {
            "final_value": float(self.dataframe["value"].iloc[-1]),
            "total_return": float(self.dataframe["cumulative_pnl"].iloc[-1]),
            "max_drawdown": float(self.dataframe["max_drawdown"].min()),
            "mar_ratio": float(self.dataframe["mar_ratio"].iloc[-1]),
        }

        return self.dataframe, summary
