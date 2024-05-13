"""app/__init__.py
Initialize the Flask application with specific configurations and setups.

This module sets up the Flask application with configurations based on the
environment. It initializes all necessary Flask extensions and registers
blueprints for different application components.
"""

import os
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import DevConfig, ProdConfig, TestConfig

def create_app(config):
    """
    Create and configure an instance of the Flask application based on the
    FLASK_CONFIG environment variable.

    :return: The configured Flask application instance.
    """
    app = Flask(__name__)

    # Configure app based on the FLASK_CONFIG environment variable
    config_type = os.getenv('FLASK_CONFIG', 'DevConfig')
    config = {
        'DevConfig': DevConfig,
        'TestConfig': TestConfig,
        'ProdConfig': ProdConfig
    }.get(config_type, DevConfig)
    app.config.from_object(config)

    # Initialize Flask extensions
    db = SQLAlchemy(app)
    Migrate(app, db)
    if app.config['SESSION_TYPE'] == 'redis':
        Session(app)

    # Import and register blueprints
    from .blackjack import blackjack_bp  # pylint: disable=C0415
    app.register_blueprint(blackjack_bp, url_prefix='/blackjack')

    return app
