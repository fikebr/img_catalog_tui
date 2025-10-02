"""
Logging module for the application.
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
import time

LOG_FORMAT = "%(asctime)s %(levelname)s %(filename)s %(funcName)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE = "logs/app.log"
LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_LEVEL_CONSOLE = logging.DEBUG
LOG_LEVEL_FILE = logging.DEBUG


class SafeTimedRotatingFileHandler(TimedRotatingFileHandler):
    """A TimedRotatingFileHandler that handles Windows file locking issues gracefully."""
    
    def doRollover(self):
        """Override doRollover to handle Windows file locking issues."""
        try:
            super().doRollover()
        except (OSError, PermissionError) as e:
            # If rollover fails, just continue logging to the current file
            # This prevents the application from crashing due to file locks
            print(f"Warning: Log rollover failed: {e}. Continuing with current log file.")


def setup_logging():
    """
    Configure logging settings for the application.

    Logs are written to a time-based rotating file that rotates daily at midnight.
    Uses a Windows-friendly approach that handles file locking issues gracefully.
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

    # Set up the safe timed rotating file handler for DEBUG and above
    # This is more Windows-friendly than RotatingFileHandler
    try:
        file_handler = SafeTimedRotatingFileHandler(
            LOG_FILE, 
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        file_handler.setLevel(LOG_LEVEL_FILE)  # File gets DEBUG and above
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not set up file logging: {e}")
        print("Continuing with console logging only...")
        # Continue without file logging if there's an issue

    # Set up console handler for INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL_CONSOLE)  # Console gets INFO and above
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console_handler)
    
    # Suppress logs from specific libraries
    logging.getLogger('PIL').setLevel(logging.WARNING)  # Suppress PIL debug and info logs
    
    logging.info("Logging initialized")
    
    return logger
