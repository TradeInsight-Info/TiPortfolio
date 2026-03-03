import os
import time


def init_tz(default_tz: str = 'America/New_York') -> None:
    """Initialize the timezone to America/Los_Angeles."""
    os.environ['TZ'] = default_tz
    
    # Compatible with Windows systems
    try:
        time.tzset()
    except AttributeError:
        # On Windows systems, the time module does not have the tzset() function.
        pass

if __name__ == "__main__":
    init_tz()