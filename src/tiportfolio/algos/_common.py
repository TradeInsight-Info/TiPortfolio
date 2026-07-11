from __future__ import annotations

import pandas as pd

from tiportfolio.algo import Context


def selected_keys(context: Context) -> list[str]:
    """Names of ``context.selected``, coercing Portfolio nodes to their ``name``.

    Every weigh algo maps the ``str | Portfolio`` items in ``context.selected``
    to plain string keys before allocating; this owns that coercion.
    """
    return [
        (item if isinstance(item, str) else item.name)
        for item in context.selected
    ]


def lookback_window(
    date: pd.Timestamp,
    lookback: pd.DateOffset,
    lag: pd.DateOffset | None = None,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Return ``(start, end)`` bounds for a lookback window ending at ``date``.

    ``lag`` shifts the window end backwards to avoid using the current bar
    (look-ahead guard). ``None`` means no lag — the window ends at ``date``
    inclusive. This is the single place the as-of convention is decided.
    """
    end = date - lag if lag is not None else date
    start = end - lookback
    return start, end
