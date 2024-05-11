"""config.py
Provide configuration variables for the Flask application.

This module defines different configuration classes for development, testing,
and production environments. Each class inherits from a base configuration
class, ensuring that all environments maintain consistent core settings while
allowing for environment-specific optimizations.
"""

import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    """Base config options."""
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Strictly fetch from environment variable
    SESSION_TYPE = 'redis'  # Change to Redis for better performance in session management
    SESSION_PERMANENT = False
    SESSION_REDIS = os.environ.get('REDIS_URL')  # Configure Redis URL

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
    """Development configuration."""
    DEBUG = True
    DATABASE_URI = os.environ.get('DEV_DATABASE_URI', 'sqlite:///dev.db')
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    DATABASE_URI = os.environ.get('TEST_DATABASE_URI', 'sqlite:///test.db')

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///prod.db')
    # Consider using a scalable SQL database system or a NoSQL solution depending on your application's needs

# To use a configuration, the environment variable FLASK_CONFIG must be set to the appropriate class name.
