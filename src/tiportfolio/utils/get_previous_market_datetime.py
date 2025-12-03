import pandas as pd
import pandas_market_calendars as mcal
from datetime import datetime


def get_previous_market_open_day(dt: datetime, market_name: str = 'NYSE') -> pd.Timestamp:
    """Return the most recent market open strictly before ``dt`` for the given market."""
    ts = pd.Timestamp(dt)
    calendar = mcal.get_calendar(market_name)

    def fetch_opens(end: pd.Timestamp, days: int) -> pd.Series:
        start_date = (end - pd.Timedelta(days=days)).date()
        end_date = end.date()
        schedule = calendar.schedule(start_date=start_date, end_date=end_date)
        return schedule.get('market_open', pd.Series(dtype='datetime64[ns]'))

    opens = fetch_opens(ts, 10)
    if opens.empty:
        opens = fetch_opens(ts, 90)
        if opens.empty:
            raise ValueError('No trading days found before the supplied datetime.')

    market_tz = opens.iloc[-1].tz
    if ts.tzinfo is None:
        ts = ts.tz_localize(market_tz)
    else:
        ts = ts.tz_convert(market_tz)

    past_opens = opens[opens < ts]
    if not past_opens.empty:
        return past_opens.iloc[-1]

    opens = fetch_opens(ts - pd.Timedelta(days=1), 365)
    past_opens = opens[opens < ts]
    if not past_opens.empty:
        return past_opens.iloc[-1]

    raise ValueError('No previous market open found within the expanded search window.')

if __name__ == "__main__":
    dt = datetime(2024, 1, 1, 10, 0)  # New Year's Day (market closed)
    print(get_previous_market_open_day(dt))