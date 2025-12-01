from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypedDict, Optional, Tuple

from pandas import DataFrame

from tiportfolio.portfolio.types import TradingSignal
from tiportfolio.utils.constants import BASIC_REQUIRED_COLUMNS


class TradingAlgorithmConfig(TypedDict, total=False):
    set_signal_back: bool  # True by default


class TradingAlgorithmStrategyResult(TypedDict):
    final_value: float
    total_return: float
    max_drawdown: float
    mar_ratio: float


class TradingAlgorithm(ABC):

    def __init__(self, name: str, symbol: str, *, prices: DataFrame, config: TradingAlgorithmConfig = None,
                 **other_data: DataFrame, ) -> None:
        self._name = name
        self._symbol = symbol
        self._set_signal_back = config.get('set_signal_back', True)
        for col in BASIC_REQUIRED_COLUMNS:
            if col not in prices.columns:
                raise ValueError(f"Data['prices'] must have '{col}' column")

        self._prices: DataFrame = prices
        self.before_all()

    def __str__(self) -> str:
        return f"Strategy({self._name} - {self._symbol})"

    def __hash__(self) -> int:
        return hash(self._name + self._symbol)

    @property
    def strategy_name(self) -> str:
        return self.__str__()

    @property
    def prices_df(self) -> DataFrame:
        return self._prices

    def _set_signal_back_to_prices_df(self, step: datetime, signal: TradingSignal) -> None:
        """
        Post run actions after each _get_signal step is complete
        We can update the column 'signal' in the prices DataFrame here
        :return: None
        """
        self._prices.loc[step, 'signal'] = signal.value

    def execute(self, step: datetime) -> TradingSignal:
        """
        Generate trading signals using the strategy function
        :param step: datetime
        :return: TradingSignal
        """
        signal = self._run(
            self._prices.loc[:step],  # we use the loc to avoid look-ahead bias
            step,
        )
        if self._set_signal_back:
            self._set_signal_back_to_prices_df(step, signal)
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
    def _run(self, history_prices: DataFrame, step: datetime, ) -> TradingSignal:
        """
        Analyse History Data and Predict Next Signal (Current Time)
        :param history_data: HistoryDataExtension
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

        if "signal" not in self.prices_df.columns:
            # Nothing to evaluate – the strategy never populated signals.
            print(f"No signals were recorded in prices DataFrame for {self._symbol}.")
            return None

        # --- Per-period PnL and equity curve ---------------------------------
        # Use explicit ``fill_method=None`` to avoid deprecated default
        # behaviour in ``pct_change`` and keep the first return as NaN. We
        # then replace NaNs with 0 so that the equity curve starts from 1.0
        # without propagating missing values.
        returns = self.prices_df["close"].pct_change(fill_method=None)

        # Use yesterday's signal for today's return; if there is no prior
        # signal yet, assume flat (0 exposure).
        shifted_signal = self.prices_df["signal"].shift(1).fillna(0)

        self.prices_df["pnl"] = (shifted_signal * returns).fillna(0)

        # Portfolio value, starting from 1.0 and compounding PnL.
        self.prices_df["value"] = (1 + self.prices_df["pnl"]).cumprod()

        # --- Aggregate performance metrics -----------------------------------
        # Cumulative PnL relative to the starting capital.
        self.prices_df["cumulative_pnl"] = self.prices_df["value"] - 1

        # Drawdown series and running maximum drawdown.
        self.prices_df["cummax"] = self.prices_df["value"].cummax()
        self.prices_df["drawdown"] = self.prices_df["value"] / self.prices_df["cummax"] - 1
        self.prices_df["max_drawdown"] = self.prices_df["drawdown"].cummin()

        # MAR ratio: total return divided by absolute maximum drawdown. Use a
        # tiny epsilon to avoid division by zero.
        max_dd_abs = self.prices_df["max_drawdown"].abs().replace(0, 1e-10)
        self.prices_df["mar_ratio"] = self.prices_df["cumulative_pnl"] / max_dd_abs

        summary: TradingAlgorithmStrategyResult = {
            "final_value": float(self.prices_df["value"].iloc[-1]),
            "total_return": float(self.prices_df["cumulative_pnl"].iloc[-1]),
            "max_drawdown": float(self.prices_df["max_drawdown"].min()),
            "mar_ratio": float(self.prices_df["mar_ratio"].iloc[-1]),
        }

        return self.prices_df, summary
