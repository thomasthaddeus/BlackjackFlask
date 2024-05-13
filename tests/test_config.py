"""test_config.py
_summary_

_extended_summary_
"""

import unittest
from unittest.mock import patch
from config import Config, DevConfig, TestConfig, ProdConfig

class TestConfigurations(unittest.TestCase):

    def test_base_config(self):
        """Test the default settings in the base config."""
        self.assertEqual(Config.SECRET_KEY, 'your_fallback_secret_key')
        self.assertEqual(Config.SESSION_TYPE, 'redis')
        self.assertFalse(Config.SESSION_PERMANENT)
        self.assertEqual(Config.SESSION_REDIS, 'redis://localhost:6379')
        self.assertEqual(Config.SQLALCHEMY_DATABASE_URI, 'sqlite:///yourdatabase.db')
        self.assertFalse(Config.SQLALCHEMY_TRACK_MODIFICATIONS)
        self.assertEqual(Config.A, 11)

    def test_dev_config(self):
        """Test the development config settings."""
        self.assertTrue(DevConfig.DEBUG)
        self.assertFalse(DevConfig.TESTING)
        self.assertEqual(DevConfig.SQLALCHELMY_DATABASE_URI, 'sqlite:///dev.db')

    def test_test_config(self):
        """Test the testing config settings."""
        self.assertTrue(TestConfig.DEBUG)
        self.assertTrue(TestConfig.TESTING)
        self.assertEqual(TestConfig.SQLALCHELMY_DATABASE_URI, 'sqlite:///test.db')

    def test_prod_config(self):
        """Test the production config settings."""
        self.assertFalse(ProdConfig.DEBUG)
        self.assertFalse(ProdConfig.TESTING)
        self.assertEqual(ProdConfig.SQLALCHELMY_DATABASE_URI, 'sqlite:///prod.db')

    @patch('os.getenv')
    def test_environment_variable_overrides(self, mock_getenv):
        """Test that environment variables correctly override defaults."""
        mock_getenv.side_effect = lambda x, default=None: {'SECRET_KEY': 'env_secret_key', 'REDIS_URL': 'redis://prod:6379'}.get(x, default)
        self.assertEqual(Config.SECRET_KEY, 'env_secret_key')
        self.assertEqual(Config.SESSION_REDIS, 'redis://prod:6379')

if __name__ == '__main__':
    unittest.main()
