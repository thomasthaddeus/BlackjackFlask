"""Configuration tests for the Flask application."""

import unittest

from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig


class TestConfigurations(unittest.TestCase):
    """Validate the current configuration classes."""

    def test_base_config_defaults(self):
        """Base config should expose the active default settings."""
        self.assertEqual(Config.SECRET_KEY, "your_fallback_secret_key")
        self.assertEqual(Config.SESSION_TYPE, "filesystem")
        self.assertFalse(Config.SESSION_PERMANENT)
        self.assertEqual(Config.SQLALCHEMY_DATABASE_URI, "sqlite:///blackjack.db")
        self.assertFalse(Config.SQLALCHEMY_TRACK_MODIFICATIONS)
        self.assertEqual(Config.A, 11)

    def test_development_config(self):
        """Development config should enable debug mode."""
        self.assertTrue(DevelopmentConfig.DEBUG)
        self.assertFalse(DevelopmentConfig.TESTING)
        self.assertEqual(DevelopmentConfig.SQLALCHEMY_DATABASE_URI, "sqlite:///dev.db")

    def test_testing_config(self):
        """Testing config should enable testing mode."""
        self.assertTrue(TestingConfig.DEBUG)
        self.assertTrue(TestingConfig.TESTING)
        self.assertEqual(TestingConfig.SQLALCHEMY_DATABASE_URI, "sqlite:///test.db")

    def test_production_config(self):
        """Production config should disable debug and testing."""
        self.assertFalse(ProductionConfig.DEBUG)
        self.assertFalse(ProductionConfig.TESTING)
        self.assertEqual(ProductionConfig.SQLALCHEMY_DATABASE_URI, "sqlite:///prod.db")


if __name__ == "__main__":
    unittest.main()
