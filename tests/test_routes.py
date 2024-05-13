"""test_routes.py
_summary_

_extended_summary_
"""

import unittest
from flask import Flask, session
from app.blackjack.routes import blackjack_bp
from app.blackjack.models import Game

class TestBlackjackRoutes(unittest.TestCase):
    def setUp(self):
        """Set up a Flask test client and register the blackjack blueprint."""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_key'  # Needed for session management in tests
        self.app.register_blueprint(blackjack_bp)
        self.client = self.app.test_client()

        # Use in-memory database for tests
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    def test_index_route(self):
        """Test the index route."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Welcome to Blackjack', response.get_data(as_text=True))

    def test_start_game(self):
        """Test starting a new game."""
        response = self.client.post('/start', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(session.get('game'), Game)
        self.assertIn('Game started', response.get_data(as_text=True))

    def test_place_bet(self):
        """Test placing a bet."""
        with self.client as client:
            client.post('/start')  # Start a game first
            response = client.post('/bet', data={'bet': 100}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(session['bet'], 100)

    def test_game_status(self):
        """Test the game status route with an active game."""
        with self.client as client:
            client.post('/start')
            response = client.get('/game_status')
            self.assertEqual(response.status_code, 200)
            self.assertIn('Current game status', response.get_data(as_text=True))

    def test_handle_action(self):
        """Test handling an action during a game."""
        with self.client as client:
            client.post('/start')
            response = client.post('/action/hit', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Performed hit', response.get_data(as_text=True))

    def test_invalid_action(self):
        """Test sending an invalid action."""
        response = self.client.post('/action/fly', follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid action', response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main()
