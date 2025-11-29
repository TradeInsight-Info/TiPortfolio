import pandas as pd
import pandas_market_calendars as mcal
from datetime import datetime, timedelta


def get_next_market_open_day(dt: datetime, market_name: str = 'NYSE') -> pd.Timestamp:
    ts = pd.Timestamp(dt)  # convert to pandas Timestamp for consistent ops
    nyse = mcal.get_calendar(market_name)

    def fetch_opens(start: pd.Timestamp, days: int):
        schedule = nyse.schedule(start_date=start.date(), end_date=(start + pd.Timedelta(days=days)).date())
        return schedule.get('market_open', pd.Series(dtype='datetime64[ns]'))

    # try initial window
    opens = fetch_opens(ts, 10)

    # expand if no schedule found
    if opens.empty:
        opens = fetch_opens(ts, 90)
        if opens.empty:
            raise ValueError("No trading days found in schedule for the search window.")

    # ensure dt is timezone-aware in market tz
    market_tz = opens.iloc[0].tz
    if ts.tzinfo is None:
        ts = ts.tz_localize(market_tz)
    else:
        ts = ts.tz_convert(market_tz)

    # find next open strictly after ts
    future_opens = opens[opens > ts]
    if not future_opens.empty:
        return future_opens.iloc[0]

    # last resort: expand forward and search again
    opens = fetch_opens(ts + pd.Timedelta(days=1), 365)
    future_opens = opens[opens > ts]
    if not future_opens.empty:
        return future_opens.iloc[0]

    raise ValueError("No future market open found within the expanded search window.")


if __name__ == "__main__":
    dt = datetime(2024, 12, 25, 14, 0)  # Christmas Day (market closed)
    print(get_next_market_open_day(dt))
