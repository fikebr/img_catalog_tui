"""
Logging module for the application.
"""

import logging
from logging.handlers import RotatingFileHandler
import os

LOG_FORMAT = "%(asctime)s %(levelname)s %(filename)s %(funcName)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE = "logs/app.log"
LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_LEVEL_CONSOLE = logging.DEBUG
LOG_LEVEL_FILE = logging.DEBUG


def setup_logging():
    """
    Configure logging settings for the application.

    Logs are written to a rotating file with a maximum size of 10 MB.
    The log format includes the date, time, log level, line number, and message.
    """
    # Configure root logger
    logger = logging.getLogger()
    
    # Clear any existing handlers to prevent duplicate messages
    logger.handlers.clear()
    
    # Set root logger to DEBUG to capture all levels
    logger.setLevel(logging.DEBUG)

    # Create the log directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError as e:
            print(f"Error creating log directory: {e}")
            return

    # Set up the rotating file handler for DEBUG and above
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=LOG_FILE_MAX_SIZE, backupCount=5
    )
    file_handler.setLevel(LOG_LEVEL_FILE)  # File gets DEBUG and above
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)

    # Set up console handler for INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL_CONSOLE)  # Console gets INFO and above
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console_handler)
    
    # Suppress logs from specific libraries
    logging.getLogger('PIL').setLevel(logging.WARNING)  # Suppress PIL debug and info logs
    
    logging.info("Logging initialized")
    
    return logger
