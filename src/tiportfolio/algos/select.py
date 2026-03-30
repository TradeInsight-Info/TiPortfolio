from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from tiportfolio.algo import Algo, Context


class Select:
    """Namespace for select algos (what to include)."""

    class All(Algo):
        """Selects all children from the portfolio."""

        def __call__(self, context: Context) -> bool:
            context.selected = list(context.portfolio.children or [])
            return True

    class Momentum(Algo):
        """Selects top-N tickers by cumulative return over a lookback window.

        Args:
            n: Number of tickers to select.
            lookback: Length of the return lookback window.
            lag: Offset from current date to avoid look-ahead bias.
            sort_descending: True for top performers, False for worst.
        """

        def __init__(
            self,
            n: int,
            lookback: pd.DateOffset,
            lag: pd.DateOffset = pd.DateOffset(days=1),
            sort_descending: bool = True,
        ) -> None:
            self._n = n
            self._lookback = lookback
            self._lag = lag
            self._sort_descending = sort_descending

        def __call__(self, context: Context) -> bool:
            end = context.date - self._lag
            start = end - self._lookback
            scores: dict[str, float] = {}
            for item in context.selected:
                if not isinstance(item, str):
                    continue
                series = context.prices[item].loc[start:end, "close"]
                scores[item] = series.pct_change().sum()
            ranked = sorted(scores, key=lambda k: scores[k], reverse=self._sort_descending)
            context.selected = ranked[: self._n]
            return True

    class Filter(Algo):
        """Boolean gate using external data. Returns False to halt the algo queue.

        Args:
            data: Dict of extra DataFrames (e.g. VIX data).
            condition: Callable receiving current-date rows, returns True/False.
        """

        def __init__(
            self,
            data: dict[str, pd.DataFrame],
            condition: Callable[[dict[str, pd.Series]], bool],
        ) -> None:
            self._data = data
            self._condition = condition

        def __call__(self, context: Context) -> bool:
            row = {ticker: df.loc[context.date] for ticker, df in self._data.items()}
            return bool(self._condition(row))
