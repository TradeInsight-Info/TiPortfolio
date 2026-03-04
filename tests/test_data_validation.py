"""Tests for data validation: ensure CSV price columns match DataFrame close columns."""

import pandas as pd
import pytest


@pytest.mark.parametrize("symbol", ["bil", "qqq", "gld"])
def test_csv_price_matches_dataframe_close(symbol):
    """Test that price column in CSV matches close column in DataFrame CSV."""
    csv_path = f"tests/data/{symbol}_2018_2024.csv"
    df_csv_path = f"tests/data/{symbol}_2018_2024_df.csv"
    
    df_csv = pd.read_csv(csv_path)
    df_df = pd.read_csv(df_csv_path)
    
    # The CSV has 'date' and symbol column with prices
    price_column = symbol.upper()
    pd.testing.assert_series_equal(
        df_csv[price_column], 
        df_df['close'], 
        check_names=False
    )
