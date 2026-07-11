from __future__ import annotations

from tiportfolio.algo import Algo, Context


class Action:
    """Namespace for action algos (execute trades)."""

    class Rebalance(Algo):
        """Triggers trade execution through the engine on Context."""

        def __call__(self, context: Context) -> bool:
            if context.engine is None:
                raise RuntimeError(
                    "Action.Rebalance: engine not set on Context"
                )
            context.engine.rebalance(context.portfolio, context)
            return True

    class PrintInfo(Algo):
        """Prints debug information about the current evaluation. Always returns True."""

        def __call__(self, context: Context) -> bool:
            print(
                f"[{context.date.date()}] portfolio={context.portfolio.name}"
                f" selected={context.selected} weights={context.weights}"
            )
            return True
