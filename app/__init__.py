"""app/__init__.py
Initialize the Flask application with specific configurations and setups.

This module sets up the Flask application with configurations based on the
environment. It initializes all necessary Flask extensions and registers
blueprints for different application components.
"""

import os
from flask import Flask
from flask_migrate import Migrate
from config import DevelopmentConfig, ProductionConfig, TestingConfig
from .extensions import db


def create_app(config=None):
    """
    Create and configure an instance of the Flask application based on the
    FLASK_CONFIG environment variable.

    :return: The configured Flask application instance.
    """
    app = Flask(__name__)
    # Configure app based on the FLASK_CONFIG environment variable
    config_type = os.getenv('FLASK_CONFIG', 'DevelopmentConfig')
    config = {
        'DevelopmentConfig': DevelopmentConfig,
        'TestingConfig': TestingConfig,
        'ProductionConfig': ProductionConfig
    }.get(config_type, DevelopmentConfig)
    app.config.from_object(config)

    # Initialize Flask extensions
    db.init_app(app)
    Migrate(app, db)
    # Removed Redis session initialization
    # if app.config.get('SESSION_TYPE') == 'redis':
    #     Session(app)

    # Import and register blueprints
    from .blackjack import blackjack_bp  # pylint: disable=C0415
    app.register_blueprint(blackjack_bp, url_prefix='/blackjack')

    return app
