import logging
import os

logger = logging.getLogger("default_logger")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())