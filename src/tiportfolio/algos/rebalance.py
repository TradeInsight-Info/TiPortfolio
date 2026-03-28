from __future__ import annotations

from tiportfolio.algo import Algo, Context
from tiportfolio.portfolio import Portfolio


class Action:
    """Namespace for action algos (execute trades)."""

    class Rebalance(Algo):
        """Triggers trade execution via engine callbacks on Context."""

        def __call__(self, context: Context) -> bool:
            children = context.portfolio.children
            is_parent = (
                children is not None
                and len(children) > 0
                and isinstance(children[0], Portfolio)
            )
            if is_parent:
                if context._allocate_children is None:
                    raise RuntimeError(
                        "Action.Rebalance: _allocate_children callback not set on Context"
                    )
                context._allocate_children(context.portfolio, context)
            else:
                if context._execute_leaf is None:
                    raise RuntimeError(
                        "Action.Rebalance: _execute_leaf callback not set on Context"
                    )
                context._execute_leaf(context.portfolio, context)
            return True

    class PrintInfo(Algo):
        """Prints debug information about the current evaluation. Always returns True."""

        def __call__(self, context: Context) -> bool:
            print(
                f"[{context.date.date()}] portfolio={context.portfolio.name}"
                f" selected={context.selected} weights={context.weights}"
            )
            return True
