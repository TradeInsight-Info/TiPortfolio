"""Integration test: verify Alpaca and YFinance return structurally compatible DataFrames.

Fetches real data for QQQ over a short window (2018-01-01 to 2018-01-31).
Skipped by default — run with ``pytest -m integration`` to include.
Alpaca tests are further skipped if ALPACA_API_KEY / ALPACA_API_SECRET are not set.
"""

from __future__ import annotations

import os

import pandas as pd
import pytest
from dotenv import load_dotenv

pytestmark = pytest.mark.integration

from tiportfolio.data import _split_flat_to_dict
from tiportfolio.helpers.data import Alpaca, YFinance

load_dotenv()

START = "2018-01-01"
END = "2018-01-31"
SYMBOLS = ["QQQ"]
REQUIRED_COLUMNS = {"date", "symbol", "open", "high", "low", "close", "volume"}
SHARED_OHLCV = {"open", "high", "low", "close", "volume"}

alpaca_key = os.environ.get("ALPACA_API_KEY", "")
alpaca_secret = os.environ.get("ALPACA_API_SECRET", "")
skip_alpaca = not (alpaca_key and alpaca_secret)


@pytest.fixture(scope="module")
def yfinance_flat() -> pd.DataFrame:
    """Fetch real data from YFinance (auto_adjust=True by default)."""
    source = YFinance()
    return source.query(SYMBOLS, START, END)


@pytest.fixture(scope="module")
def alpaca_flat() -> pd.DataFrame:
    """Fetch real data from Alpaca."""
    source = Alpaca(api_key=alpaca_key, api_secret=alpaca_secret)
    return source.query(SYMBOLS, START, END, timeframe="1d")


@pytest.fixture(scope="module")
def yfinance_normalized(yfinance_flat: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """YFinance data after _split_flat_to_dict normalization."""
    return _split_flat_to_dict(yfinance_flat)


@pytest.fixture(scope="module")
def alpaca_normalized(alpaca_flat: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Alpaca data after _split_flat_to_dict normalization."""
    return _split_flat_to_dict(alpaca_flat)


class TestYFinanceFlat:
    """Verify YFinance raw DataFrame structure."""

    def test_contains_required_columns(self, yfinance_flat: pd.DataFrame) -> None:
        assert REQUIRED_COLUMNS.issubset(yfinance_flat.columns)

    def test_no_adj_close_with_auto_adjust(self, yfinance_flat: pd.DataFrame) -> None:
        assert "adj_close" not in yfinance_flat.columns

    def test_has_no_vwap(self, yfinance_flat: pd.DataFrame) -> None:
        assert "vwap" not in yfinance_flat.columns

    def test_dates_are_tz_naive(self, yfinance_flat: pd.DataFrame) -> None:
        dates = pd.to_datetime(yfinance_flat["date"])
        assert dates.dt.tz is None

    def test_returns_data(self, yfinance_flat: pd.DataFrame) -> None:
        assert len(yfinance_flat) > 0


@pytest.mark.skipif(skip_alpaca, reason="ALPACA_API_KEY / ALPACA_API_SECRET not set")
class TestAlpacaFlat:
    """Verify Alpaca raw DataFrame structure."""

    def test_contains_required_columns(self, alpaca_flat: pd.DataFrame) -> None:
        assert REQUIRED_COLUMNS.issubset(alpaca_flat.columns)

    def test_has_vwap(self, alpaca_flat: pd.DataFrame) -> None:
        assert "vwap" in alpaca_flat.columns

    def test_has_no_adj_close(self, alpaca_flat: pd.DataFrame) -> None:
        assert "adj_close" not in alpaca_flat.columns

    def test_dates_are_tz_aware(self, alpaca_flat: pd.DataFrame) -> None:
        dates = pd.to_datetime(alpaca_flat["date"])
        assert dates.dt.tz is not None

    def test_returns_data(self, alpaca_flat: pd.DataFrame) -> None:
        assert len(alpaca_flat) > 0


@pytest.mark.skipif(skip_alpaca, reason="ALPACA_API_KEY / ALPACA_API_SECRET not set")
class TestCrossSourceParity:
    """Compare both sources side by side."""

    def test_shared_columns_match(
        self, yfinance_flat: pd.DataFrame, alpaca_flat: pd.DataFrame
    ) -> None:
        assert REQUIRED_COLUMNS.issubset(yfinance_flat.columns)
        assert REQUIRED_COLUMNS.issubset(alpaca_flat.columns)

    def test_only_vwap_differs(
        self, yfinance_flat: pd.DataFrame, alpaca_flat: pd.DataFrame
    ) -> None:
        yf_extra = set(yfinance_flat.columns) - set(alpaca_flat.columns)
        alp_extra = set(alpaca_flat.columns) - set(yfinance_flat.columns)
        assert yf_extra == set(), f"YFinance-only: {yf_extra}"
        assert alp_extra == {"vwap"}, f"Alpaca-only: {alp_extra}"

    def test_same_trading_days(
        self, yfinance_flat: pd.DataFrame, alpaca_flat: pd.DataFrame
    ) -> None:
        yf_dates = pd.to_datetime(yfinance_flat["date"]).dt.date.unique()
        alp_dates = pd.to_datetime(alpaca_flat["date"]).dt.date.unique()
        assert set(yf_dates) == set(alp_dates), (
            f"Date mismatch — YF only: {set(yf_dates) - set(alp_dates)}, "
            f"Alpaca only: {set(alp_dates) - set(yf_dates)}"
        )


@pytest.mark.skipif(skip_alpaca, reason="ALPACA_API_KEY / ALPACA_API_SECRET not set")
class TestNormalizedParity:
    """After _split_flat_to_dict, both sources should produce aligned output."""

    def test_both_have_utc_index(
        self,
        yfinance_normalized: dict[str, pd.DataFrame],
        alpaca_normalized: dict[str, pd.DataFrame],
    ) -> None:
        for df in yfinance_normalized.values():
            assert str(df.index.tz) == "UTC"
        for df in alpaca_normalized.values():
            assert str(df.index.tz) == "UTC"

    def test_same_tickers(
        self,
        yfinance_normalized: dict[str, pd.DataFrame],
        alpaca_normalized: dict[str, pd.DataFrame],
    ) -> None:
        assert set(yfinance_normalized.keys()) == set(alpaca_normalized.keys())

    def test_same_index(
        self,
        yfinance_normalized: dict[str, pd.DataFrame],
        alpaca_normalized: dict[str, pd.DataFrame],
    ) -> None:
        for ticker in yfinance_normalized:
            assert yfinance_normalized[ticker].index.equals(
                alpaca_normalized[ticker].index
            ), f"{ticker} index mismatch after normalization"

    def test_shared_ohlcv_columns(
        self,
        yfinance_normalized: dict[str, pd.DataFrame],
        alpaca_normalized: dict[str, pd.DataFrame],
    ) -> None:
        for ticker in yfinance_normalized:
            assert SHARED_OHLCV.issubset(yfinance_normalized[ticker].columns)
            assert SHARED_OHLCV.issubset(alpaca_normalized[ticker].columns)
