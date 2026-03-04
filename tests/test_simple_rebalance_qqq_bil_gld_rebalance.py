"""Simple rebalance backtest: QQQ/BIL/GLD with tests/data CSVs; summary and decisions match saved CSVs."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from tiportfolio import ScheduleBasedEngine, FixRatio, Schedule, rebalance_decisions_table
from tiportfolio.data import load_csv


DATA_DIR = Path(__file__).resolve().parent / "data"

# 70% QQQ, 20% BIL, 10% GLD, start-of-month rebalance
WEIGHTS = {"QQQ": 0.7, "BIL": 0.2, "GLD": 0.1}
START = "2018-01-01"
END = "2024-12-31"
INITIAL_VALUE = 10_000
FEE_PER_SHARE = 0.0035


def _load_qqq_bil_gld_prices():
    """Load the 3 price CSVs (column name = symbol)."""
    symbols = list(WEIGHTS.keys())
    prices = {}
    for s in symbols:
        path = DATA_DIR / f"{s.lower()}_{START[:4]}_{END[:4]}.csv"
        prices[s] = load_csv(path, symbol=s, price_column=s)
    return prices


def test_simple_rebalance_qqq_bil_gld_summary_matches_csv():
    """Backtest with QQQ/BIL/GLD config; metrics match summary CSV."""
    prices = _load_qqq_bil_gld_prices()
    symbols = list(WEIGHTS.keys())
    engine = ScheduleBasedEngine(
        allocation=FixRatio(weights=WEIGHTS),
        rebalance=Schedule("month_start"),
        fee_per_share=FEE_PER_SHARE,
        initial_value=INITIAL_VALUE,
    )
    result = engine.run(symbols=symbols, prices_df=prices, start=START, end=END)

    expected_summary = pd.read_csv(DATA_DIR / "qqq_bil_gld_2018_2024_summary.csv")
    assert len(expected_summary) == 1
    row = expected_summary.iloc[0]

    assert result.metrics["sharpe_ratio"] == pytest.approx(row["sharpe_ratio"], rel=1e-9)
    assert result.metrics["cagr"] == pytest.approx(row["cagr"], rel=1e-9)
    assert result.metrics["max_drawdown"] == pytest.approx(row["max_drawdown"], rel=1e-9)
    assert result.metrics["mar_ratio"] == pytest.approx(row["mar_ratio"], rel=1e-9)
    assert result.metrics["kelly_leverage"] == pytest.approx(row["kelly_leverage"], rel=1e-9)


def test_simple_rebalance_qqq_bil_gld_decisions_match_csv():
    """Backtest with QQQ/BIL/GLD config; rebalance decisions match decisions CSV."""
    prices = _load_qqq_bil_gld_prices()
    symbols = list(WEIGHTS.keys())
    engine = ScheduleBasedEngine(
        allocation=FixRatio(weights=WEIGHTS),
        rebalance=Schedule("month_start"),
        fee_per_share=FEE_PER_SHARE,
        initial_value=INITIAL_VALUE,
    )
    result = engine.run(symbols=symbols, prices_df=prices, start=START, end=END)

    decisions = rebalance_decisions_table(result)
    expected = pd.read_csv(DATA_DIR / "qqq_bil_gld_2018_2024_decisions.csv")
    expected["date"] = pd.to_datetime(expected["date"], utc=True)

    assert len(decisions) == len(expected)
    assert list(decisions.columns) == list(expected.columns)

    # Compare numeric columns with tolerance (decisions table rounds to 3 decimals)
    num_cols = decisions.select_dtypes(include=[np.number]).columns
    for c in num_cols:
        np.testing.assert_allclose(
            decisions[c].astype(float),
            expected[c].astype(float),
            rtol=1e-5,
            err_msg=f"Column {c}",
        )
    # Compare dates (as datetime64 for consistent comparison)
    np.testing.assert_array_equal(
        pd.to_datetime(decisions["date"], utc=True).values.astype("datetime64[us]"),
        pd.to_datetime(expected["date"], utc=True).values.astype("datetime64[us]"),
    )
