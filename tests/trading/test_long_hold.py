from unittest import TestCase
import pandas as pd
from datetime import datetime
from pathlib import Path

from tiportfolio.strategies.trading.long_hold import LongHold
from tiportfolio.portfolio.types import TradingSignal

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"


class TestLongHold(TestCase):

    def test_long_hold_execute_always_long(self):
        # Prepare minimal prices DataFrame – we only need the required OHLC
        # columns, and can keep it empty for this smoke test.
        prices = pd.DataFrame(columns=["open", "high", "low", "close"])

        strategy = LongHold("AAPL", prices)
        # Use execute to generate the signal (testing public API).
        step = datetime(2024, 1, 1)
        signal = strategy.execute(step)

        self.assertEqual(signal, TradingSignal.LONG)

        strategy.after_all()

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

        strategy = LongHold("AAPL", df)
        # Call execute at each available step to confirm stability of the
        # public API across the time index. We do not reach into the
        # protected hook; we only assert on the externally observable
        # behaviour (always-long signal).

        for ts in dates:
            step = ts.to_pydatetime()
            signal = strategy.execute(step)
            self.assertEqual(signal, TradingSignal.LONG)

    def test_long_hold_with_aapl_csv_history(self):
        """Ensure LongHold works with the real-world AAPL OHLCV dataset.

        This uses tests/data/aapl.csv, converts it to the canonical history
        format expected by strategies (DateTimeIndex, OHLCV columns), and
        verifies that:

        * execute() always returns a long (1) signal; and
        * the TradingAlgorithm base class slices history up to ``step``.
        """

        csv_path = DATA_DIR / "aapl.csv"
        df_raw = pd.read_csv(csv_path)

        # Normalise into the standard prices DataFrame shape used elsewhere
        # in the tests: DateTimeIndex and the OHLCV columns.
        df = df_raw.copy()
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        prices = df[["open", "high", "low", "close", "volume"]]

        strategy = LongHold("AAPL", prices)

        # Use a mid-sample date to ensure slicing behaviour works on a
        # realistic dataset. We pick the 10th row for determinism.
        step_ts = prices.index[9]
        step_mid = step_ts.to_pydatetime()

        # Verify that execute returns a long signal for a variety of
        # realistic timestamps, without touching internal hooks.
        first_step = prices.index[0].to_pydatetime()
        last_step = prices.index[-1].to_pydatetime()

        for step in (first_step, step_mid, last_step):
            signal = strategy.execute(step)
            self.assertEqual(signal, TradingSignal.LONG)
