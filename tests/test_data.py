from __future__ import annotations

from typing import Any
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


# ---------------------------------------------------------------------------
# fetch_data with csv parameter
# ---------------------------------------------------------------------------


class TestFetchDataCSV:
    def _write_csv(self, path: str, ticker: str, n: int = 5) -> None:
        """Write a minimal per-ticker CSV file."""
        dates = pd.bdate_range("2024-01-02", periods=n, freq="B")
        dates = dates.tz_localize("UTC")
        df = pd.DataFrame(
            {
                "open": [100.0 + i for i in range(n)],
                "high": [101.0 + i for i in range(n)],
                "low": [99.0 + i for i in range(n)],
                "close": [100.5 + i for i in range(n)],
                "volume": [1_000_000.0] * n,
            },
            index=dates,
        )
        df.index.name = "date"
        df.to_csv(path)

    def test_csv_dict_loads_files(self, tmp_path: Any) -> None:
        """csv={ticker: path} bypasses network and loads from CSV."""
        csv_qqq = str(tmp_path / "qqq.csv")
        csv_bil = str(tmp_path / "bil.csv")
        self._write_csv(csv_qqq, "QQQ")
        self._write_csv(csv_bil, "BIL")

        result = fetch_data(
            ["QQQ", "BIL"],
            start="2024-01-01",
            end="2024-02-01",
            csv={"QQQ": csv_qqq, "BIL": csv_bil},
        )
        assert set(result.keys()) == {"QQQ", "BIL"}
        assert "close" in result["QQQ"].columns
        assert isinstance(result["QQQ"].index, pd.DatetimeIndex)
        assert str(result["QQQ"].index.tz) == "UTC"

    def test_csv_dir_auto_discovers(self, tmp_path: Any) -> None:
        """csv='path/to/dir' auto-discovers <ticker>.csv files."""
        self._write_csv(str(tmp_path / "QQQ.csv"), "QQQ")
        self._write_csv(str(tmp_path / "BIL.csv"), "BIL")

        result = fetch_data(
            ["QQQ", "BIL"],
            start="2024-01-01",
            end="2024-02-01",
            csv=str(tmp_path),
        )
        assert set(result.keys()) == {"QQQ", "BIL"}

    def test_csv_dir_case_insensitive(self, tmp_path: Any) -> None:
        """csv dir lookup should find lowercase filenames for uppercase tickers."""
        self._write_csv(str(tmp_path / "qqq.csv"), "QQQ")

        result = fetch_data(
            ["QQQ"],
            start="2024-01-01",
            end="2024-02-01",
            csv=str(tmp_path),
        )
        assert "QQQ" in result

    def test_csv_missing_ticker_raises(self, tmp_path: Any) -> None:
        """Missing CSV file raises FileNotFoundError."""
        self._write_csv(str(tmp_path / "QQQ.csv"), "QQQ")

        with pytest.raises(FileNotFoundError, match="GLD"):
            fetch_data(
                ["QQQ", "GLD"],
                start="2024-01-01",
                end="2024-02-01",
                csv=str(tmp_path),
            )

    def test_csv_dict_missing_ticker_raises(self, tmp_path: Any) -> None:
        """Partial csv dict raises FileNotFoundError listing missing tickers."""
        csv_qqq = str(tmp_path / "qqq.csv")
        self._write_csv(csv_qqq, "QQQ")

        with pytest.raises(FileNotFoundError, match="BIL") as exc_info:
            fetch_data(
                ["QQQ", "BIL", "GLD"],
                start="2024-01-01",
                end="2024-02-01",
                csv={"QQQ": csv_qqq},
            )
        # Both missing tickers should be listed in one error
        assert "GLD" in str(exc_info.value)

    def test_csv_dir_multiple_missing_raises_all(self, tmp_path: Any) -> None:
        """Directory mode collects all missing tickers in one error."""
        self._write_csv(str(tmp_path / "QQQ.csv"), "QQQ")

        with pytest.raises(FileNotFoundError, match="BIL") as exc_info:
            fetch_data(
                ["QQQ", "BIL", "GLD"],
                start="2024-01-01",
                end="2024-02-01",
                csv=str(tmp_path),
            )
        assert "GLD" in str(exc_info.value)

    def test_csv_skips_network(self, tmp_path: Any) -> None:
        """When csv is provided, no network call is made."""
        self._write_csv(str(tmp_path / "QQQ.csv"), "QQQ")

        with patch("tiportfolio.data._query_yfinance") as mock_yf:
            fetch_data(["QQQ"], start="2024-01-01", end="2024-02-01", csv=str(tmp_path))
            mock_yf.assert_not_called()
