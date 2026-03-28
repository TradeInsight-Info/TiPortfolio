from __future__ import annotations

import pandas as pd
import pytest

from tiportfolio.config import TiConfig
from tiportfolio.result import BacktestResult, _SingleResult


def _make_single_result(name: str = "test") -> _SingleResult:
    dates = pd.date_range("2024-01-02", periods=20, freq="B", tz="UTC")
    # Simulated equity curve: starts at 10000, grows ~0.5% per day
    values = [10000 * (1.005**i) for i in range(20)]
    equity = pd.Series(values, index=dates, name="equity")
    return _SingleResult(name=name, equity_curve=equity, config=TiConfig())


class TestSingleResult:
    def test_equity_curve_access(self) -> None:
        sr = _make_single_result()
        assert isinstance(sr.equity_curve, pd.Series)
        assert len(sr.equity_curve) == 20

    def test_name(self) -> None:
        sr = _make_single_result("myport")
        assert sr.name == "myport"

    def test_summary_returns_dataframe(self) -> None:
        sr = _make_single_result()
        df = sr.summary()
        assert isinstance(df, pd.DataFrame)

    def test_summary_has_key_metrics(self) -> None:
        sr = _make_single_result()
        df = sr.summary()
        metrics = df.index.tolist()
        assert "total_return" in metrics
        assert "cagr" in metrics
        assert "max_drawdown" in metrics
        assert "sharpe" in metrics

    def test_total_return_positive(self) -> None:
        sr = _make_single_result()
        df = sr.summary()
        tr = df.loc["total_return", "value"]
        assert tr > 0  # growing equity → positive return


class TestBacktestResult:
    def test_int_index(self) -> None:
        sr = _make_single_result("port1")
        br = BacktestResult([sr])
        assert br[0].name == "port1"

    def test_string_index(self) -> None:
        sr = _make_single_result("port1")
        br = BacktestResult([sr])
        assert br["port1"].name == "port1"

    def test_invalid_string_raises(self) -> None:
        sr = _make_single_result("port1")
        br = BacktestResult([sr])
        with pytest.raises(KeyError):
            br["nonexistent"]

    def test_invalid_int_raises(self) -> None:
        sr = _make_single_result("port1")
        br = BacktestResult([sr])
        with pytest.raises(IndexError):
            br[5]

    def test_summary_delegates(self) -> None:
        sr = _make_single_result("port1")
        br = BacktestResult([sr])
        df = br.summary()
        assert isinstance(df, pd.DataFrame)
