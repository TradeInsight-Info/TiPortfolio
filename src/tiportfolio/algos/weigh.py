from __future__ import annotations

import math

import pandas as pd

from tiportfolio.algo import Algo, Context


class Weigh:
    """Namespace for weigh algos (how much to allocate)."""

    class Equally(Algo):
        """Divides capital equally across context.selected."""

        def __init__(self, short: bool = False) -> None:
            self._short = short

        def __call__(self, context: Context) -> bool:
            n = len(context.selected)
            if n == 0:
                return True
            sign = -1.0 if self._short else 1.0
            context.weights = {
                (item if isinstance(item, str) else item.name): sign / n
                for item in context.selected
            }
            return True

    class Ratio(Algo):
        """Assigns explicit weights, normalised to sum(|w|) = 1.0.

        Args:
            weights: Dict mapping ticker/name to target weight.
                     Tickers in selected but missing from weights get weight 0.
        """

        def __init__(self, weights: dict[str, float]) -> None:
            self._weights = weights

        def __call__(self, context: Context) -> bool:
            keys = [
                (item if isinstance(item, str) else item.name)
                for item in context.selected
            ]
            raw = {k: self._weights[k] for k in keys if k in self._weights}
            total = sum(abs(v) for v in raw.values()) or 1.0
            context.weights = {k: v / total for k, v in raw.items()}
            return True

    class BasedOnHV(Algo):
        """Scales initial_ratio to target annualised portfolio volatility.

        Uses diagonal covariance approximation:
        portfolio_hv = sqrt(sum((w * hv)^2))

        Args:
            initial_ratio: Starting weight allocation per ticker.
            target_hv: Target annualised volatility as decimal (0.15 = 15%).
            lookback: Window for computing historical volatility.
        """

        def __init__(
            self,
            initial_ratio: dict[str, float],
            target_hv: float,
            lookback: pd.DateOffset,
        ) -> None:
            self._initial_ratio = initial_ratio
            self._target_hv = target_hv
            self._lookback = lookback

        def __call__(self, context: Context) -> bool:
            start = context.date - self._lookback
            end = context.date
            bars_per_year = context.config.bars_per_year

            keys = [
                (item if isinstance(item, str) else item.name)
                for item in context.selected
            ]

            hv: dict[str, float] = {}
            for ticker in keys:
                if ticker not in context.prices:
                    continue
                series = context.prices[ticker].loc[start:end, "close"]
                daily_returns = series.pct_change().dropna()
                hv[ticker] = float(daily_returns.std() * math.sqrt(bars_per_year))

            # Diagonal covariance approximation
            portfolio_hv = math.sqrt(
                sum(
                    (self._initial_ratio.get(t, 0.0) * hv.get(t, 0.0)) ** 2
                    for t in keys
                )
            )

            if portfolio_hv == 0.0:
                context.weights = dict(self._initial_ratio)
                return True

            scale = self._target_hv / portfolio_hv
            context.weights = {
                t: self._initial_ratio.get(t, 0.0) * scale for t in keys
            }
            return True
