from __future__ import annotations

from tiportfolio.algo import Algo, Context


class Select:
    """Namespace for select algos (what to include)."""

    class All(Algo):
        """Selects all children from the portfolio."""

        def __call__(self, context: Context) -> bool:
            context.selected = list(context.portfolio.children or [])
            return True
