"""Route tests for the blackjack Flask blueprint."""

import unittest

from app import create_app


class TestBlackjackRoutes(unittest.TestCase):
    """Exercise the current JSON and HTML route flow."""

    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test_key")
        self.client = self.app.test_client()

    def test_root_route_redirects_to_blackjack(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/blackjack/", response.headers["Location"])

    def test_index_route(self):
        response = self.client.get("/blackjack/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Welcome to Blackjack", response.get_data(as_text=True))

    def test_start_game_returns_waiting_for_bet_state(self):
        response = self.client.post("/blackjack/start")
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["awaitingBet"])
        self.assertEqual(data["playerHand"], "No cards dealt yet.")

    def test_place_bet_deals_a_new_hand(self):
        with self.client as client:
            client.post("/blackjack/start")
            response = client.post("/blackjack/bet", json={"bet": 25})
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertFalse(data["awaitingBet"])
            self.assertEqual(data["currentBet"], 25)
            self.assertNotEqual(data["playerHand"], "No cards dealt yet.")
            self.assertIn("Hidden", data["dealerHand"])

    def test_cannot_place_bet_during_active_round(self):
        with self.client as client:
            client.post("/blackjack/start")
            client.post("/blackjack/bet", json={"bet": 25})
            response = client.post("/blackjack/bet", json={"bet": 10})
            self.assertEqual(response.status_code, 400)
            self.assertIn("Finish the current hand", response.get_json()["error"])

    def test_game_status(self):
        with self.client as client:
            client.post("/blackjack/start")
            client.post("/blackjack/bet", json={"bet": 15})
            response = client.get("/blackjack/game_status")
            self.assertEqual(response.status_code, 200)
            self.assertIn("Current Game Status", response.get_data(as_text=True))

    def test_handle_action_requires_bet_first(self):
        with self.client as client:
            client.post("/blackjack/start")
            response = client.post("/blackjack/action/hit")
            self.assertEqual(response.status_code, 400)
            self.assertIn("Place a bet", response.get_json()["error"])

    def test_handle_hit_action(self):
        with self.client as client:
            client.post("/blackjack/start")
            client.post("/blackjack/bet", json={"bet": 20})
            response = client.post("/blackjack/action/hit")
            self.assertEqual(response.status_code, 200)
            self.assertIn("playerHand", response.get_json())

    def test_invalid_action(self):
        with self.client as client:
            client.post("/blackjack/start")
            client.post("/blackjack/bet", json={"bet": 20})
            response = client.post("/blackjack/action/fly")
            self.assertEqual(response.status_code, 400)
            self.assertIn("Invalid action", response.get_json()["error"])

    def test_new_game_preserves_bankroll(self):
        with self.client as client:
            client.post("/blackjack/start")
            client.post("/blackjack/bet", json={"bet": 10})
            surrender_response = client.post("/blackjack/action/surrender")
            bankroll_after_surrender = surrender_response.get_json()["bankroll"]

            restart_response = client.post("/blackjack/start")
            restart_data = restart_response.get_json()
            self.assertEqual(restart_response.status_code, 200)
            self.assertEqual(restart_data["bankroll"], bankroll_after_surrender)
            self.assertTrue(restart_data["awaitingBet"])


if __name__ == "__main__":
    unittest.main()
