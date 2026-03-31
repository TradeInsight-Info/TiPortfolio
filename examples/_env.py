"""Shared preamble for example scripts — loads .env from project root."""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Offline CSV data mapping
# ---------------------------------------------------------------------------
# Pre-downloaded YFinance CSV files for 6 tickers (2018-2024).
# Pass as csv= parameter to ti.fetch_data() for offline/faster runs.
# Without csv=, fetch_data() requires network access.

_DATA_DIR = Path(__file__).resolve().parent.parent / "tests" / "data"

CSV_DATA: dict[str, str] = {
    "AAPL": str(_DATA_DIR / "aapl_2018_2024_yf.csv"),
    "QQQ": str(_DATA_DIR / "qqq_2018_2024_yf.csv"),
    "BIL": str(_DATA_DIR / "bil_2018_2024_yf.csv"),
    "GLD": str(_DATA_DIR / "gld_2018_2024_yf.csv"),
    "^VIX": str(_DATA_DIR / "vix_2018_2024_yf.csv"),
    "^VVIX": str(_DATA_DIR / "vvix_2018_2024_yf.csv"),
}
