"""
app/__init__.py
Initialize the Flask application with specific configurations and setups.

This module sets up the Flask application with configurations based on the
environment. It initializes all necessary Flask extensions and registers
blueprints for different application components.
"""

from flask import Flask
from flask_session import Session  # Import the session management extension
from config import DevelopmentConfig, ProductionConfig, TestingConfig
import logging

def create_app():
    """
    Create and configure an instance of the Flask application based on the FLASK_CONFIG environment variable.

    :return: The configured Flask application instance.
    """
    config_name = os.getenv('FLASK_CONFIG', 'DevelopmentConfig')
    config_class = {
        'DevelopmentConfig': DevelopmentConfig,
        'TestingConfig': TestingConfig,
        'ProductionConfig': ProductionConfig
    }.get(config_name, DevelopmentConfig)

    app = Flask(__name__)
    app.config.from_object(config_class)  # Dynamically load configuration

    # Initialize Flask extensions
    Session(app)  # Initialize session management with app

    # Import and register blueprints
    from .blackjack import blackjack_bp  # Make sure the import path is correct based on your project structure
    app.register_blueprint(blackjack_bp, url_prefix='/blackjack')

    # Additional setups can be added here
    if app.config['DEBUG']:
        # Setup for debug mode: logging, debug tools, etc.
        app.logger.setLevel(logging.DEBUG)
    elif app.config['TESTING']:
        # Additional setup for testing environment
        app.logger.setLevel(logging.CRITICAL)
    else:
        # Production-specific setup
        app.logger.setLevel(logging.WARNING)

    return app

# Note: Ensure that all necessary modules and packages are correctly installed and available in your environment
