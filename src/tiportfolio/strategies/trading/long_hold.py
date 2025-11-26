from ...portfolio.strategy import Strategy


class LongHold(Strategy):

    def __init__(self) -> None:
        super().__init__("LongHold")

    # Implement the dunder hook using base class name-mangled identifier
    # so it properly overrides Strategy.__analyse_next_signal
    def _analyse_next_signal(self, history_data) -> int:  # type: ignore[override]
        """
        Always return long signal
        :param history_data: HistoryDataExtension
        :return: 1 (long)
        """
        return 1
