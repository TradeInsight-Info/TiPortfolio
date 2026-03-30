from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


DATA_DIR = Path(__file__).parent / "data"


# ---------------------------------------------------------------------------
# Auto-skip integration tests unless explicitly requested
# ---------------------------------------------------------------------------

def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip tests marked ``@pytest.mark.integration`` unless the user passes
    ``-m integration`` (or ``--run-integration``) on the command line."""
    keyword_expr = config.option.markexpr  # value of ``-m``
    if keyword_expr and "integration" in keyword_expr:
        return  # user explicitly asked for integration tests
    skip_marker = pytest.mark.skip(reason="integration test — pass -m integration to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_marker)


# ---------------------------------------------------------------------------
# Synthetic fixtures for unit tests (controlled prices, small date range)
# ---------------------------------------------------------------------------

_SYNTHETIC_DATES = pd.bdate_range("2024-01-02", "2024-02-01", freq="B")


def _make_synthetic_ticker(ticker: str, base_price: float) -> pd.DataFrame:
    """Generate simple synthetic OHLCV rows for one ticker."""
    n = len(_SYNTHETIC_DATES)
    rows = []
    for i in range(n):
        o = base_price + i * 0.5
        rows.append(
            {
                "date": _SYNTHETIC_DATES[i],
                "symbol": ticker,
                "open": o,
                "high": o + 1.5,
                "low": o - 0.5,
                "close": o + 1.0,
                "volume": float(1_000_000 + i * 10_000),
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture()
def prices_flat() -> pd.DataFrame:
    """Raw flat DataFrame with symbol/date columns — mimics DataSource.query() output."""
    frames = [
        _make_synthetic_ticker("QQQ", 100.0),
        _make_synthetic_ticker("BIL", 90.55),
        _make_synthetic_ticker("GLD", 185.0),
    ]
    return pd.concat(frames, ignore_index=True)


@pytest.fixture()
def prices_dict(prices_flat: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Per-ticker dict with UTC DatetimeIndex — the format the engine expects."""
    result: dict[str, pd.DataFrame] = {}
    for symbol, group in prices_flat.groupby("symbol"):
        df = group.drop(columns=["symbol"]).copy()
        df = df.set_index("date")
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")
        df.columns = [c.lower() for c in df.columns]
        result[str(symbol)] = df.sort_index()
    return result


@pytest.fixture()
def trading_dates(prices_dict: dict[str, pd.DataFrame]) -> pd.DatetimeIndex:
    """Sorted union of all trading dates across tickers."""
    all_dates: set[pd.Timestamp] = set()
    for df in prices_dict.values():
        all_dates.update(df.index)
    return pd.DatetimeIndex(sorted(all_dates))


# ---------------------------------------------------------------------------
# Real data fixtures for integration tests
# ---------------------------------------------------------------------------


def load_yf_ticker(ticker: str) -> pd.DataFrame:
    """Load a per-ticker yf CSV with UTC DatetimeIndex."""
    name = ticker.lower().replace("^", "")
    path = DATA_DIR / f"{name}_2018_2024_yf.csv"
    df = pd.read_csv(path, index_col="date", parse_dates=True)
    return df
