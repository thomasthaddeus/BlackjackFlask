"""Launch the Flask application using environment-specific configurations."""

import argparse
import os
from dotenv import load_dotenv
from app import create_app
from app.utils import setup_logging

load_dotenv()


def parse_args():
    """Parse runtime options for the development server."""
    parser = argparse.ArgumentParser(description="Run the Blackjack Flask app.")
    parser.add_argument(
        "--log-level",
        choices=["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"],
        help="Enable loguru logging at the selected level.",
    )
    return parser.parse_args()


config_name = os.getenv('FLASK_CONFIG', 'DevelopmentConfig')
app = create_app(config_name)


def main():
    """Run the Flask development server."""
    args = parse_args()
    if args.log_level:
        os.environ["BLACKJACK_LOG_LEVEL"] = args.log_level

    logger = setup_logging("run", os.getenv("BLACKJACK_LOG_LEVEL", "WARNING"))
    logger.info(
        "Starting server with config {config_name} on port {port}",
        config_name=config_name,
        port=os.getenv('PORT', '5001'),
    )

    if app.config['DEBUG'] is False:
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5001')), debug=False)
    else:
        app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5001')), debug=True)


if __name__ == "__main__":
    main()
