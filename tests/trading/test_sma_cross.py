from unittest import TestCase
from datetime import datetime
import pandas as pd

from tiportfolio.strategies.trading.sma_cross import SMACross


class TestSMACross(TestCase):

    def setUp(self) -> None:
        # Construct a more complex dataset with clear uptrend then downtrend
        dates = pd.date_range(start="2024-01-01", periods=12, freq="D")
        close = [10, 10, 10, 10, 10, 11, 12, 13, 13, 12, 11, 10]
        df = pd.DataFrame(
            {
                "open": close,
                "high": [c * 1.01 for c in close],
                "low": [c * 0.99 for c in close],
                "close": close,
                "volume": [100 + i * 10 for i in range(len(close))],
            },
            index=pd.to_datetime(dates),
        )
        self.data = {"prices": df}
        self.strategy = SMACross(short_window=3, long_window=5)

    def test_insufficient_data_returns_neutral(self):
        # With step at the 4th day, long_window (5) not met -> 0
        step = datetime(2024, 1, 4)
        signal = self.strategy.execute(self.data, step)
        self.assertEqual(signal, 0)

    def test_golden_cross_signal(self):
        # Expected golden cross at 2024-01-06 for the constructed series
        # Verify just before is neutral, at the day is long (1)
        pre_step = datetime(2024, 1, 5)
        step = datetime(2024, 1, 6)

        self.assertEqual(self.strategy.execute(self.data, pre_step), 0)
        self.assertEqual(self.strategy.execute(self.data, step), 1)

    def test_death_cross_signal(self):
        # Expected death cross at 2024-01-11 for the constructed series
        pre_step = datetime(2024, 1, 10)
        step = datetime(2024, 1, 11)

        self.assertIn(self.strategy.execute(self.data, pre_step), (0, 1))
        self.assertEqual(self.strategy.execute(self.data, step), -1)


class TestSMACrossLargeDataset(TestCase):

    @staticmethod
    def _build_large_prices(n: int = 300) -> pd.DataFrame:
        # Build a 300-row piecewise series designed to create both golden and death crosses
        # Segments: 60 flat at 100, 80 up to 140, 40 flat at 140, 80 down to 100, 40 flat at 100
        assert n == 300, "This helper is tailored for 300 rows"
        seg1 = [100.0] * 60
        seg2 = [100.0 + 0.5 * i for i in range(80)]  # 100 -> 139.5
        seg3 = [140.0] * 40
        seg4 = [140.0 - 0.5 * i for i in range(80)]  # 140 -> 100.5
        seg5 = [100.0] * 40
        close = seg1 + seg2 + seg3 + seg4 + seg5
        dates = pd.date_range(start="2024-01-01", periods=n, freq="D")
        df = pd.DataFrame(
            {
                "open": close,
                "high": [c * 1.01 for c in close],
                "low": [c * 0.99 for c in close],
                "close": close,
                "volume": [1000 + i for i in range(n)],
            },
            index=pd.to_datetime(dates),
        )
        return df

    @staticmethod
    def _expected_signals(df: pd.DataFrame, short_window: int, long_window: int) -> list[int]:
        closes = df["close"].astype(float)
        s_sma = closes.rolling(window=short_window, min_periods=short_window).mean()
        l_sma = closes.rolling(window=long_window, min_periods=long_window).mean()

        # Shift to get previous values
        prev_s = s_sma.shift(1)
        prev_l = l_sma.shift(1)

        # Conditions aligned with strategy logic
        golden = (prev_s <= prev_l) & (s_sma > l_sma)
        death = (prev_s >= prev_l) & (s_sma < l_sma)

        exp = []
        for i in range(len(df)):
            # Insufficient data or NaNs -> 0
            if pd.isna(s_sma.iloc[i]) or pd.isna(l_sma.iloc[i]) or pd.isna(prev_s.iloc[i]) or pd.isna(prev_l.iloc[i]):
                exp.append(0)
                continue
            if golden.iloc[i]:
                exp.append(1)
            elif death.iloc[i]:
                exp.append(-1)
            else:
                exp.append(0)
        return exp

    def test_large_dataset_multiple_windows_and_signal_variety(self):
        df = self._build_large_prices(300)
        data = {"prices": df}

        window_pairs = [(5, 20), (10, 50)]
        for sw, lw in window_pairs:
            strat = SMACross(short_window=sw, long_window=lw)

            # Compute expected signals for each date
            expected = self._expected_signals(df, sw, lw)

            # Collect actual signals by executing at each step
            actual: list[int] = []
            for ts in df.index:
                sig = strat.execute(data, ts.to_pydatetime())
                actual.append(sig)

            # Full-sequence equality
            self.assertEqual(actual, expected, f"Signals mismatch for windows ({sw},{lw})")

            # Ensure we have all three signal types present in the run
            unique = set(actual)
            self.assertIn(1, unique, f"No long signals detected for windows ({sw},{lw})")
            self.assertIn(-1, unique, f"No short signals detected for windows ({sw},{lw})")
            self.assertIn(0, unique, f"No exit/neutral signals detected for windows ({sw},{lw})")
