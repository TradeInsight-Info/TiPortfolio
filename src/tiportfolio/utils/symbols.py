from __future__ import annotations

from .constants import VOLATILITY_INDEX_SYMBOLS as VOLATILITY_SYMBOLS


def normalize_volatility_symbol(symbol: str) -> str:
    """Return symbol without ^ and uppercased; validate against VOLATILITY_SYMBOLS."""
    s = symbol.strip().upper().lstrip("^")
    if s not in VOLATILITY_SYMBOLS:
        raise ValueError(
            f"volatility_symbol must be one of {VOLATILITY_SYMBOLS}; got {symbol!r}"
        )
    return s
