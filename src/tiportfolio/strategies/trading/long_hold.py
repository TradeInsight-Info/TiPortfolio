from datetime import datetime

from pandas import DataFrame

from ...portfolio.trading_algorithm import TradingAlgorithm, TradingAlgorithmConfig
from ...portfolio.types import TradingSignal


class LongHold(TradingAlgorithm):

    def __init__(self, symbol: str, prices: DataFrame) -> None:
        config:TradingAlgorithmConfig = {"set_signal_back": False}
        super().__init__("LongHold", symbol, config=config, prices=prices,)

    def before_all(self) -> None:  # type: ignore[override]
        """No-op data preparation.

        The long-hold strategy does not require any indicators, so we simply
        honour the abstract hook from :class:`TradingAlgorithm`.
        """
        return None

    def _run(self, history_prices: DataFrame, step: datetime) -> TradingSignal:  # type: ignore[override]
        """Always return :data:`TradingSignal.LONG`.

        Parameters
        ----------
        history_prices:
            Slice of the prices DataFrame up to ``step``. This argument is
            provided by :meth:`TradingAlgorithm.execute` and is ignored by
            this strategy since it is unconditional.
        step:
            Current timestamp of the backtest/run. Present for API
            consistency with other strategies and ignored here.
        """

        signal = TradingSignal.LONG
        return signal

    def after_all(self) -> None:
        """No-op post-run actions.

        The long-hold strategy does not require any post-run processing, so we
        simply honour the abstract hook from :class:`TradingAlgorithm`.
        """

        # fromt prices find how many long, hold, exit, short signals there were

        if 'signal' not in self.prices_df.columns:
            print(f"No signals were recorded in prices DataFrame for {self._symbol}.")
            return

        long_count = (self.prices_df['signal'] == TradingSignal.LONG.value).sum()
        hold_count = (self.prices_df['signal'] == TradingSignal.HOLD.value).sum()
        exit_count = (self.prices_df['signal'] == TradingSignal.EXIT.value).sum()
        short_count = (self.prices_df['signal'] == TradingSignal.SHORT.value).sum()

        print(f"LongHold Strategy Summary for {self._symbol}:")
        print(f"  LONG signals: {long_count}")
        print(f"  HOLD signals: {hold_count}")
        print(f"  EXIT signals: {exit_count}")
        print(f"  SHORT signals: {short_count}")
