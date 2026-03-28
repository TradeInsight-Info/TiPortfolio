from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from tiportfolio.config import TiConfig


@dataclass
class Context:
    """Passed to every Algo.__call__. Carries read-only inputs and mutable inter-algo state."""

    # read-only inputs
    portfolio: Any  # Portfolio (Any to avoid circular import at runtime)
    prices: dict[str, pd.DataFrame]
    date: pd.Timestamp
    config: TiConfig

    # mutable inter-algo communication
    selected: list[Any] = field(default_factory=list)  # list[str | Portfolio]
    weights: dict[str, float] = field(default_factory=dict)

    # engine callbacks — set by engine before calling algo_queue
    _execute_leaf: Callable[..., None] | None = field(default=None, repr=False)
    _allocate_children: Callable[..., None] | None = field(default=None, repr=False)


class Algo(ABC):
    """Base class for all algo-stack components."""

    @abstractmethod
    def __call__(self, context: Context) -> bool:
        """Return True to continue the AlgoQueue, False to abort."""


class AlgoQueue(Algo):
    """Runs algos sequentially. Short-circuits on the first False."""

    def __init__(self, algos: list[Algo]) -> None:
        self._algos = algos

    def __call__(self, context: Context) -> bool:
        return all(algo(context) for algo in self._algos)
