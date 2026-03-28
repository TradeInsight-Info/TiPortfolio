from __future__ import annotations

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
