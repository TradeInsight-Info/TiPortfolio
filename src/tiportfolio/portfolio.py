from __future__ import annotations

from typing import Any

from tiportfolio.algo import Algo, AlgoQueue


class Portfolio:
    """Tree node holding mutable simulation state.

    Args:
        name: Display name for this portfolio node.
        algos: Ordered list of algos forming the strategy pipeline.
        children: Leaf tickers (list of str) or child Portfolio nodes.
    """

    def __init__(
        self,
        name: str,
        algos: list[Algo],
        children: list[str] | list[Any] | None,  # list[str] | list[Portfolio] | None
    ) -> None:
        self.name = name
        self.algo_queue = AlgoQueue(algos)
        self.children = children

        # mutable state — updated by engine on every bar
        self.positions: dict[str, float] = {}
        self.cash: float = 0.0
        self.equity: float = 0.0
