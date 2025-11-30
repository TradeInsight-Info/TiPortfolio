import os
import time


def init_tz(default_tz: str = 'America/New_York') -> None:
    """Initialize the timezone to America/Los_Angeles."""
    os.environ['TZ'] = default_tz
    time.tzset()


if __name__ == "__main__":
    init_tz()