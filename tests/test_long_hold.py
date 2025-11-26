from unittest import TestCase
import pandas as pd
from datetime import datetime

from tiportfolio.strategies.trading.long_hold import LongHold


class TestLongHold(TestCase):

    def test_long_hold_execute_always_long(self):
        # Prepare minimal history data with an empty prices DataFrame
        history_data = {"prices": pd.DataFrame()}

        strategy = LongHold()
        # Use execute to generate the signal (testing public API)
        step = datetime(2024, 1, 1)
        signal = strategy.execute(history_data, step)

        self.assertEqual(signal, 1)

    def test_long_hold_execute_returns_long_and_slices_history(self):
        # Create a simple prices DataFrame with a DateTimeIndex
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])  # type: ignore[list-item]
        df = pd.DataFrame(
            {
                "open": [1.0, 2.0, 3.0],
                "high": [1.1, 2.1, 3.1],
                "low": [0.9, 1.9, 2.9],
                "close": [1.05, 2.05, 3.05],
                "volume": [100, 200, 300],
            },
            index=dates,
        )

        strategy = LongHold()
        captured = {}

        # Monkeypatch the protected hook on the instance to capture sliced history
        def _capture(self, history_data):  # type: ignore[unused-argument]
            captured["history_data"] = history_data
            return 1

        # Bind the capturing function to the instance under the protected hook name
        strategy._analyse_next_signal = _capture.__get__(strategy, LongHold)  # type: ignore[attr-defined]

        all_data = {"prices": df}
        step = datetime(2024, 1, 2)
        signal = strategy.execute(all_data, step)

        # Verify the signal is long
        self.assertEqual(signal, 1)

        # Verify the history_data was sliced up to and including the step
        self.assertIn("history_data", captured)
        sliced = captured["history_data"]["prices"]
        self.assertIsInstance(sliced, pd.DataFrame)
        self.assertEqual(sliced.index.max(), pd.Timestamp(step))
        self.assertEqual(len(sliced), 2)
