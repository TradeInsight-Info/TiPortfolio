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
            result = fetch_data(
                ["QQQ", "BIL", "GLD"], start="2024-01-01", end="2024-02-01", source="yfinance"
            )
        assert set(result.keys()) == {"QQQ", "BIL", "GLD"}

    def test_dataframe_has_correct_columns(self, prices_flat: pd.DataFrame) -> None:
        with patch("tiportfolio.data._query_yfinance", return_value=prices_flat):
            result = fetch_data(
                ["QQQ", "BIL", "GLD"], start="2024-01-01", end="2024-02-01", source="yfinance"
            )
        for ticker, df in result.items():
            assert "close" in df.columns
            assert "open" in df.columns
            assert "volume" in df.columns

    def test_index_is_utc_datetime(self, prices_flat: pd.DataFrame) -> None:
        with patch("tiportfolio.data._query_yfinance", return_value=prices_flat):
            result = fetch_data(["QQQ"], start="2024-01-01", end="2024-02-01", source="yfinance")
        idx = result["QQQ"].index
        assert isinstance(idx, pd.DatetimeIndex)
        assert str(idx.tz) == "UTC"

    def test_no_symbol_column_in_output(self, prices_flat: pd.DataFrame) -> None:
        with patch("tiportfolio.data._query_yfinance", return_value=prices_flat):
            result = fetch_data(["QQQ"], start="2024-01-01", end="2024-02-01", source="yfinance")
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


# ---------------------------------------------------------------------------
# fetch_data provider selection (tidata -> alpaca -> yfinance)
# ---------------------------------------------------------------------------


def _clear_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("TRADEINSIGHT_API_KEY", "ALPACA_API_KEY", "ALPACA_API_SECRET"):
        monkeypatch.delenv(var, raising=False)


class TestFetchDataProviderSelection:
    def test_auto_prefers_tidata(
        self, monkeypatch: pytest.MonkeyPatch, prices_flat: pd.DataFrame
    ) -> None:
        _clear_keys(monkeypatch)
        monkeypatch.setenv("TRADEINSIGHT_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_KEY", "a")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        with patch("tiportfolio.data._query_tidata", return_value=prices_flat) as t, \
             patch("tiportfolio.data._query_alpaca") as a, \
             patch("tiportfolio.data._query_yfinance") as y:
            fetch_data(["QQQ", "BIL", "GLD"], start="2024-01-01", end="2024-02-01")
        t.assert_called_once()
        a.assert_not_called()
        y.assert_not_called()

    def test_auto_uses_alpaca_when_only_alpaca_keys(
        self, monkeypatch: pytest.MonkeyPatch, prices_flat: pd.DataFrame
    ) -> None:
        _clear_keys(monkeypatch)
        monkeypatch.setenv("ALPACA_API_KEY", "a")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        with patch("tiportfolio.data._query_tidata") as t, \
             patch("tiportfolio.data._query_alpaca", return_value=prices_flat) as a, \
             patch("tiportfolio.data._query_yfinance") as y:
            fetch_data(["QQQ", "BIL", "GLD"], start="2024-01-01", end="2024-02-01")
        t.assert_not_called()
        a.assert_called_once()
        y.assert_not_called()

    def test_auto_falls_back_to_yfinance_without_keys(
        self, monkeypatch: pytest.MonkeyPatch, prices_flat: pd.DataFrame
    ) -> None:
        _clear_keys(monkeypatch)
        with patch("tiportfolio.data._query_tidata") as t, \
             patch("tiportfolio.data._query_alpaca") as a, \
             patch("tiportfolio.data._query_yfinance", return_value=prices_flat) as y:
            fetch_data(["QQQ", "BIL", "GLD"], start="2024-01-01", end="2024-02-01")
        t.assert_not_called()
        a.assert_not_called()
        y.assert_called_once()

    def test_auto_falls_through_on_provider_error(
        self, monkeypatch: pytest.MonkeyPatch, prices_flat: pd.DataFrame
    ) -> None:
        """tidata available but failing -> chain continues to alpaca."""
        _clear_keys(monkeypatch)
        monkeypatch.setenv("TRADEINSIGHT_API_KEY", "k")
        monkeypatch.setenv("ALPACA_API_KEY", "a")
        monkeypatch.setenv("ALPACA_API_SECRET", "s")
        with patch("tiportfolio.data._query_tidata", side_effect=RuntimeError("boom")) as t, \
             patch("tiportfolio.data._query_alpaca", return_value=prices_flat) as a, \
             patch("tiportfolio.data._query_yfinance") as y:
            result = fetch_data(["QQQ", "BIL", "GLD"], start="2024-01-01", end="2024-02-01")
        t.assert_called_once()
        a.assert_called_once()
        y.assert_not_called()
        assert set(result.keys()) == {"QQQ", "BIL", "GLD"}

    def test_explicit_source_ignores_env(
        self, monkeypatch: pytest.MonkeyPatch, prices_flat: pd.DataFrame
    ) -> None:
        """source='yfinance' forces yfinance even when a tidata key is set."""
        _clear_keys(monkeypatch)
        monkeypatch.setenv("TRADEINSIGHT_API_KEY", "k")
        with patch("tiportfolio.data._query_tidata") as t, \
             patch("tiportfolio.data._query_yfinance", return_value=prices_flat) as y:
            fetch_data(
                ["QQQ", "BIL", "GLD"], start="2024-01-01", end="2024-02-01", source="yfinance"
            )
        t.assert_not_called()
        y.assert_called_once()

    def test_explicit_source_does_not_fall_back(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Forcing an unavailable provider raises rather than substituting."""
        _clear_keys(monkeypatch)
        with pytest.raises(RuntimeError, match="ALPACA_API_KEY"):
            fetch_data(["QQQ"], start="2024-01-01", end="2024-02-01", source="alpaca")

    def test_unknown_source_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_keys(monkeypatch)
        with pytest.raises(ValueError, match="Unknown source"):
            fetch_data(["QQQ"], start="2024-01-01", end="2024-02-01", source="nope")


# ---------------------------------------------------------------------------
# TiData adapter shape
# ---------------------------------------------------------------------------


class _FakeTicker:
    """Stand-in for tidata.tifinance.Ticker returning a synthetic daily frame."""

    def __init__(self, symbol: str, api_key: str | None = None, **kwargs: Any) -> None:
        self._symbol = symbol

    def history(self, **kwargs: Any) -> pd.DataFrame:
        idx = pd.date_range("2024-01-02", periods=5, freq="B")  # tz-naive
        idx.name = "Date"
        return pd.DataFrame(
            {
                "Open": [100.0 + i for i in range(5)],
                "High": [101.0 + i for i in range(5)],
                "Low": [99.0 + i for i in range(5)],
                "Close": [100.5 + i for i in range(5)],
                "Volume": [1_000_000] * 5,
            },
            index=idx,
        )


class TestTiDataAdapter:
    def test_query_returns_flat_contract(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("tiportfolio.helpers.data.Ticker", _FakeTicker)
        from tiportfolio.helpers.data import TiData

        flat = TiData(api_key="k").query(["QQQ"], "2024-01-01", "2024-02-01")
        assert {"symbol", "date", "open", "high", "low", "close", "volume"}.issubset(
            flat.columns
        )
        assert (flat["symbol"] == "QQQ").all()
        assert flat["date"].dt.tz is None  # tz-naive, like YFinance

    def test_fetch_data_tidata_output_shape(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_keys(monkeypatch)
        monkeypatch.setenv("TRADEINSIGHT_API_KEY", "k")
        monkeypatch.setattr("tiportfolio.helpers.data.Ticker", _FakeTicker)

        result = fetch_data(
            ["QQQ"], start="2024-01-01", end="2024-02-01", source="tidata"
        )
        assert set(result.keys()) == {"QQQ"}
        idx = result["QQQ"].index
        assert isinstance(idx, pd.DatetimeIndex)
        assert str(idx.tz) == "UTC"
        assert "symbol" not in result["QQQ"].columns
        assert "close" in result["QQQ"].columns


class TestAlignIndices:
    """_split_flat_to_dict aligns per-ticker frames to their common dates so
    providers that fetch per symbol (e.g. tidata) don't produce misaligned
    indices that break validate_data downstream."""

    def _flat(self, symbol: str, dates: pd.DatetimeIndex) -> pd.DataFrame:
        n = len(dates)
        return pd.DataFrame(
            {
                "date": dates,
                "symbol": symbol,
                "open": [100.0] * n,
                "high": [101.0] * n,
                "low": [99.0] * n,
                "close": [100.5] * n,
                "volume": [1_000_000.0] * n,
            }
        )

    def test_differing_histories_are_intersected(self) -> None:
        from tiportfolio.data import _split_flat_to_dict

        full = pd.bdate_range("2024-01-02", periods=10, tz="UTC")
        late = full[3:]  # a ticker that "listed" 3 bars later
        flat = pd.concat(
            [self._flat("SPY", full), self._flat("COIN", late)], ignore_index=True
        )
        result = _split_flat_to_dict(flat)
        # Both tickers restricted to the shared (intersection) dates.
        assert result["SPY"].index.equals(result["COIN"].index)
        assert len(result["SPY"]) == len(late)
        # And the aligned data validates.
        validate_data(result)
