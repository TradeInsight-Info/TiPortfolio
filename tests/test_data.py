"""Tests for data loading and normalization."""

import pytest

from tiportfolio.data import (
    load_csvs,
    merge_prices,
    normalize_prices,
    validate_prices_keys,
)


def test_load_csvs_yields_dict_with_date_index(data_dir):
    """Loading tests/data CSVs yields dict of DataFrames with datetime index."""
    paths = [data_dir / "qqq.csv", data_dir / "spy.csv", data_dir / "gld.csv"]
    result = load_csvs(paths)
    assert isinstance(result, dict)
    assert set(result.keys()) >= {"QQQ", "SPY", "GLD"}
    for sym, df in result.items():
        assert hasattr(df.index, "name"), f"{sym} should have index"
        assert len(df.columns) == 1
        assert df.index.name in ("date", None) or "date" in str(df.index.name).lower()


def test_merge_prices_common_date_index(data_dir):
    """Merged DataFrame has common date index and one column per symbol."""
    paths = [data_dir / "qqq.csv", data_dir / "spy.csv", data_dir / "gld.csv"]
    prices = load_csvs(paths)
    merged = merge_prices(prices)
    assert merged.index.name == "date"
    assert set(merged.columns) == set(prices.keys())
    assert merged.index.is_monotonic_increasing or len(merged) <= 1


def test_validate_prices_keys_raises_on_mismatch():
    """validate_prices_keys raises when keys don't match allocation."""
    import pandas as pd
    prices = {"A": pd.DataFrame({"close": [1.0]}), "B": pd.DataFrame({"close": [1.0]})}
    validate_prices_keys(prices, {"A", "B"})  # ok
    with pytest.raises(ValueError, match="missing keys"):
        validate_prices_keys(prices, {"A", "B", "C"})
    with pytest.raises(ValueError, match="extra keys"):
        validate_prices_keys(prices, {"A"})


def test_normalize_prices_returns_merged_dataframe(data_dir):
    """normalize_prices validates and returns merged DataFrame."""
    paths = [data_dir / "spy.csv", data_dir / "qqq.csv"]
    prices = load_csvs(paths)
    allocation_keys = set(prices.keys())
    merged = normalize_prices(prices, allocation_keys)
    assert merged.shape[1] == len(allocation_keys)
    assert merged.index.name == "date"
