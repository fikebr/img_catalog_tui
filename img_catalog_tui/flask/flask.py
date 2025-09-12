"""Simple Flask application boilerplate."""

import logging
from flask import Flask

from img_catalog_tui.logger import setup_logging
from img_catalog_tui.config import Config

from . import urls

# Use the existing logging setup
logger = setup_logging()
if logger is None:
    logger = logging.getLogger(__name__)

# Load configuration once at startup
config = Config()
config.load()

app = Flask(__name__)


urls.register_routes(app)


@app.errorhandler(404)
def not_found(error) -> tuple[dict, int]:
    """Handle 404 errors."""
    logger.warning(f"404 error: {error}")
    return {"error": "Not found"}, 404


@app.errorhandler(500)
def internal_error(error) -> tuple[dict, int]:
    """Handle 500 errors."""
    logger.error(f"500 error: {error}")
    return {"error": "Internal server error"}, 500


# Route definitions



def main() -> None:
    """Main entry point for the Flask application."""
    try:
        logger.info("Starting Flask application")
        app.run(debug=True, host='127.0.0.1', port=5000)
    except Exception as e:
        logger.error(f"Failed to start Flask application: {e}")
        raise


if __name__ == '__main__':
    main()