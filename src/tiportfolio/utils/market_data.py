import yfinance as yf
from tiportfolio.utils.default_logger import logger

def fetch_beta(symbol: str) -> float:
    """
    Fetch the Beta value for a given ticker symbol from Yahoo Finance.
    
    Args:
        symbol: The ticker symbol (e.g., 'AAPL', 'VOO').
        
    Returns:
        The beta value as a float.
        
    Raises:
        ValueError: If the beta value is not found or cannot be retrieved.
    """
    try:
        logger.info(f"Fetching Beta value for {symbol} from Yahoo Finance...")
        ticker = yf.Ticker(symbol)
        beta = ticker.info.get('beta')
        
        if beta is None:
            raise ValueError(f"Beta value not found for symbol '{symbol}'. Please provide risk multipliers explicitly.")
            
        return float(beta)
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Failed to fetch beta for symbol '{symbol}': {e}. Please provide risk multipliers explicitly.")
