"""config.py
Provide configuration variables for the Flask application.

This module defines different configuration classes for development, testing,
and production environments. Each class inherits from a base configuration
class, ensuring that all environments maintain consistent core settings while
allowing for environment-specific optimizations.
"""

import os
from dotenv import load_dotenv
from redis import Redis
load_dotenv()

class Config:
    """Base config options."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_fallback_secret_key')
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    SESSION_REDIS = os.getenv('REDIS_URL', 'redis://localhost:6379')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///blackjack.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_USE_SIGNER = True

    # Constants for card values, assuming these are static across the game logic
    T, J, Q, K = 10, 10, 10, 10
    A = 11  # Initial value for an Ace

    # Card combinations for blackjack strategy
    A2 = [A, 2]
    A3 = [A, 3]
    A4 = [A, 4]
    A5 = [A, 5]
    A6 = [A, 6]
    A7 = [A, 7]
    A8 = [A, 8]

    # doubles
    D2 = [2, 2]
    D3 = [3, 3]
    D4 = [4, 4]
    D5 = [5, 5]
    D6 = [6, 6]
    D7 = [7, 7]
    D8 = [8, 8]
    D9 = [9, 9]
    DT = [T, T] or [J, J] or [Q, Q] or [K, K]
    AA = [A, A]


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SQLALCHELMY_DATABASE_URI = os.getenv('DEV_DB_URI', 'sqlite:///dev.db')

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHELMY_DATABASE_URI = os.getenv('TEST_DB_URI', 'sqlite:///test.db')

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHELMY_DATABASE_URI = os.getenv('PROD_DB_URI', 'sqlite:///prod.db')

# To use a configuration, the environment variable FLASK_CONFIG must be set to the appropriate class name.
