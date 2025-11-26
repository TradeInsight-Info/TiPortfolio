from logging import Logger


def get_logger(name: str) -> Logger:
    """Get a logger instance by name.

    Args:
        name (str): The name of the logger.

    Returns:
        Logger: The logger instance.
    """
    import logging

    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        # Configure logger if it has no handlers
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger


default_logger = get_logger("tiportfolio")