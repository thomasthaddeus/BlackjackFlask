"""
app/__init__.py
Initialize the Flask application with specific configurations and setups.

This module sets up the Flask application with configurations based on the
environment. It initializes all necessary Flask extensions and registers
blueprints for different application components.
"""

import os
from flask import Flask
from flask_session import Session
from config import DevelopmentConfig, ProductionConfig, TestingConfig

def create_app(config_name):
    """
    Create and configure an instance of the Flask application based on the
    FLASK_CONFIG environment variable.

    :return: The configured Flask application instance.
    """
    config_name = os.getenv('FLASK_CONFIG', 'DevelopmentConfig')
    config_class = {
        'DevelopmentConfig': DevelopmentConfig,
        'TestingConfig': TestingConfig,
        'ProductionConfig': ProductionConfig
    }.get(config_name, DevelopmentConfig)

    app = Flask(__name__)
    app.config.from_object(config_class)  # Apply configuration

    # Initialize Flask extensions
    if app.config['SESSION_TYPE'] == 'redis':
        Session(app)

    # Import and register blueprints
    from .blackjack import blackjack_bp  # pylint: disable=C0415
    app.register_blueprint(blackjack_bp, url_prefix='/blackjack')

    return app
