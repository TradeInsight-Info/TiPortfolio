from unittest import TestCase
from datetime import datetime
from pathlib import Path
import pandas as pd

from tiportfolio.strategy_library.trading.sma_cross import SMACross
from tiportfolio.portfolio.types import TradingSignal

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parent / "data"


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
        self.prices = df
        self.strategy = SMACross("TEST", self.prices, short_window=3, long_window=5)

    def test_insufficient_data_returns_neutral(self):
        # With step at the 4th day, long_window (5) not met -> 0
        step = datetime(2024, 1, 4)
        signal = self.strategy.execute(step)
        self.assertEqual(signal, TradingSignal.EXIT)

    def test_golden_cross_signal(self):
        # Expected golden cross at 2024-01-06 for the constructed series
        # Verify just before is neutral, at the day is long (1)
        pre_step = datetime(2024, 1, 5)
        step = datetime(2024, 1, 6)

        self.assertEqual(self.strategy.execute(pre_step), TradingSignal.EXIT)
        self.assertEqual(self.strategy.execute(step), TradingSignal.EXIT)

        ## continuelly futher it should reutn HOLD
        post_step = datetime(2024, 1, 7)
        self.assertEqual(self.strategy.execute(post_step), TradingSignal.LONG)
        post_step2 = datetime(2024, 1, 8)
        self.assertEqual(self.strategy.execute(post_step2), TradingSignal.LONG)
        post_step3 = datetime(2024, 1, 9)
        self.assertEqual(self.strategy.execute(post_step3), TradingSignal.LONG)
        post_step4 = datetime(2024, 1, 10)
        self.assertEqual(self.strategy.execute(post_step4), TradingSignal.LONG)

    def test_death_cross_signal(self):
        # Expected death cross at 2024-01-11 for the constructed series
        pre_step = datetime(2024, 1, 10)
        step = datetime(2024, 1, 11)

        self.assertIn(
            self.strategy.execute(pre_step),
            (TradingSignal.EXIT, TradingSignal.LONG),
        )
        self.assertEqual(self.strategy.execute(step), TradingSignal.SHORT)
        post_step = datetime(2024, 1, 12)
        self.assertEqual(self.strategy.execute(post_step), TradingSignal.SHORT)

    def test_walk_through_all(self):
        results = []
        for step in self.prices.index:
            result = self.strategy.execute(step)
            results.append((step, result))

        self.assertEqual(
            results,
            [
                (pd.Timestamp("2024-01-01 00:00:00"), TradingSignal.EXIT),
                (pd.Timestamp("2024-01-02 00:00:00"), TradingSignal.EXIT),
                (pd.Timestamp("2024-01-03 00:00:00"), TradingSignal.EXIT),
                (pd.Timestamp("2024-01-04 00:00:00"), TradingSignal.EXIT),
                (pd.Timestamp("2024-01-05 00:00:00"), TradingSignal.EXIT),
                (pd.Timestamp("2024-01-06 00:00:00"), TradingSignal.EXIT),
                (pd.Timestamp("2024-01-07 00:00:00"), TradingSignal.LONG),
                (pd.Timestamp("2024-01-08 00:00:00"), TradingSignal.LONG),
                (pd.Timestamp("2024-01-09 00:00:00"), TradingSignal.LONG),
                (pd.Timestamp("2024-01-10 00:00:00"), TradingSignal.LONG),
                (pd.Timestamp("2024-01-11 00:00:00"), TradingSignal.SHORT),
                (pd.Timestamp("2024-01-12 00:00:00"), TradingSignal.SHORT),
            ],
            self.strategy.prices_df
        )


class TestSMACrossWithQQQCSV(TestCase):

    def setUp(self):
        csv_path = DATA_DIR / "qqq.csv"
        df_qqq = pd.read_csv(
            csv_path,
            header=0,  # first line is headers (this is actually the default)
            index_col="date",  # use the "date" column as the index
            parse_dates=["date"]  # automatically convert that column to datetime
        )

        start = pd.Timestamp("2020-02-01", tz="America/New_York")
        end = pd.Timestamp("2020-05-01", tz="America/New_York")

        # filter from 2020-02-01 to 2020-05-01 about 3 months, 63 rows
        df_qqq = df_qqq[(df_qqq.index >= start) & (df_qqq.index <= end)]

        print(f"Filtered QQQ data has {len(df_qqq)} rows.")

        self.assertEqual(len(df_qqq), 63, "Filtered QQQ data should not be empty.")

        self.strategy = SMACross(
            "QQQ",
            prices=df_qqq,
            short_window=5,
            long_window=20,
        )

        self.strategy.before_all()
        print(self.strategy.prices_df.tail(60))

    def test_always_passes(self):
        self.assertTrue(True)

    def test_on_march_2_be_exit(self):
        step = pd.Timestamp("2020-03-02", tz="America/New_York")
        signal = self.strategy.execute(step)
        self.assertEqual(signal, TradingSignal.EXIT, 'because there is no cross yet')

    def test_on_march_3_be_short(self):
        step = pd.Timestamp("2020-03-03", tz="America/New_York")
        signal = self.strategy.execute(step)
        self.assertEqual(signal, TradingSignal.SHORT, 'because continue lower')

    def test_on_martch_31_be_long(self):
        step = pd.Timestamp("2020-04-01", tz="America/New_York")
        signal = self.strategy.execute(step)
        self.assertEqual(signal, TradingSignal.LONG, 'because short SMA crosses above long SMA on this day')

        # next day should be HOLD
        next_step = pd.Timestamp("2020-04-02", tz="America/New_York")
        next_signal = self.strategy.execute(next_step)
        self.assertEqual(next_signal, TradingSignal.LONG, 'because it should hold the LONG position')

    def test_to_run_from_start_to_end(self):
        # Run through all dates to ensure no exceptions
        results = []
        for step in self.strategy.prices_df.index:
            result = self.strategy.execute(step)
            results.append((step, result))

        expected = [
            (pd.Timestamp('2020-02-03 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-04 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-05 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-06 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-07 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-10 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-11 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-12 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-13 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-14 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-18 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-19 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-20 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-21 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-24 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-25 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-26 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-27 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-02-28 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-03-02 00:00:00-0500', tz='UTC-05:00'), TradingSignal.EXIT),
            (pd.Timestamp('2020-03-03 00:00:00-0500', tz='UTC-05:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-04 00:00:00-0500', tz='UTC-05:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-05 00:00:00-0500', tz='UTC-05:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-06 00:00:00-0500', tz='UTC-05:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-09 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-10 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-11 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-12 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-13 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-16 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-17 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-18 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-19 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-20 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-23 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-24 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-25 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-26 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-27 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-30 00:00:00-0400', tz='UTC-04:00'), TradingSignal.SHORT),
            (pd.Timestamp('2020-03-31 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-01 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-02 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-03 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-06 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-07 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-08 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-09 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-13 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-14 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-15 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-16 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-17 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-20 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-21 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-22 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-23 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-24 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-27 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-28 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-29 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-04-30 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
            (pd.Timestamp('2020-05-01 00:00:00-0400', tz='UTC-04:00'), TradingSignal.LONG),
        ]
        self.assertEqual(results, expected, self.strategy.prices_df)
