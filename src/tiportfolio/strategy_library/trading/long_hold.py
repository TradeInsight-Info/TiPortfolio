from datetime import datetime

from pandas import DataFrame

from tiportfolio.portfolio.trading_algorithm import TradingAlgorithm, TradingAlgorithmConfig
from ...portfolio.types import TradingSignal


class LongHold(TradingAlgorithm):

    def __init__(self, symbol: str, prices: DataFrame) -> None:
        config:TradingAlgorithmConfig = {"set_signal_back": True}
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
            consistency with other strategy_library and ignored here.
        """

        signal = TradingSignal.LONG
        return signal
