from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tiportfolio.data import fetch_data, validate_data


# ---------------------------------------------------------------------------
# validate_data
# ---------------------------------------------------------------------------


class TestValidateDataAligned:
    def test_aligned_passes(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        validate_data(prices_dict)  # should not raise

    def test_single_ticker_passes(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        validate_data({"QQQ": prices_dict["QQQ"]})


class TestValidateDataMisaligned:
    def test_misaligned_raises(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        bad = prices_dict.copy()
        bad["BAD"] = prices_dict["QQQ"].iloc[:-2]  # 2 fewer dates
        with pytest.raises(ValueError, match="BAD"):
            validate_data(bad)

    def test_extra_data_misaligned_raises(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        extra_df = prices_dict["QQQ"].iloc[:-3]
        with pytest.raises(ValueError, match="EXTRA"):
            validate_data(prices_dict, extra={"EXTRA": extra_df})

    def test_extra_data_aligned_passes(self, prices_dict: dict[str, pd.DataFrame]) -> None:
        extra = {"EXTRA": prices_dict["QQQ"].copy()}
        validate_data(prices_dict, extra=extra)  # should not raise


# ---------------------------------------------------------------------------
# fetch_data
# ---------------------------------------------------------------------------


class TestFetchData:
    def test_returns_dict_keyed_by_ticker(self, prices_flat: pd.DataFrame) -> None:
        with patch("tiportfolio.data._query_yfinance", return_value=prices_flat):
            result = fetch_data(["QQQ", "BIL", "GLD"], start="2024-01-01", end="2024-02-01")
        assert set(result.keys()) == {"QQQ", "BIL", "GLD"}

    def test_dataframe_has_correct_columns(self, prices_flat: pd.DataFrame) -> None:
        with patch("tiportfolio.data._query_yfinance", return_value=prices_flat):
            result = fetch_data(["QQQ", "BIL", "GLD"], start="2024-01-01", end="2024-02-01")
        for ticker, df in result.items():
            assert "close" in df.columns
            assert "open" in df.columns
            assert "volume" in df.columns

    def test_index_is_utc_datetime(self, prices_flat: pd.DataFrame) -> None:
        with patch("tiportfolio.data._query_yfinance", return_value=prices_flat):
            result = fetch_data(["QQQ"], start="2024-01-01", end="2024-02-01")
        idx = result["QQQ"].index
        assert isinstance(idx, pd.DatetimeIndex)
        assert str(idx.tz) == "UTC"

    def test_no_symbol_column_in_output(self, prices_flat: pd.DataFrame) -> None:
        with patch("tiportfolio.data._query_yfinance", return_value=prices_flat):
            result = fetch_data(["QQQ"], start="2024-01-01", end="2024-02-01")
        assert "symbol" not in result["QQQ"].columns
