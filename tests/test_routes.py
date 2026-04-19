"""Route tests for the blackjack Flask blueprint."""

import unittest

from app import create_app


class TestBlackjackRoutes(unittest.TestCase):
    """Exercise the current JSON and HTML route flow."""

    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test_key")
        self.client = self.app.test_client()

    def _start_active_round(self, client, bet=25):
        for _ in range(10):
            client.post("/blackjack/start")
            response = client.post("/blackjack/bet", json={"bet": bet})
            data = response.get_json()
            if response.status_code == 200 and not data["awaitingBet"]:
                return response
        self.fail("Could not start an active non-blackjack round after multiple attempts.")

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
            response = self._start_active_round(client, bet=25)
            data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertFalse(data["awaitingBet"])
            self.assertEqual(data["currentBet"], 25)
            self.assertNotEqual(data["playerHand"], "No cards dealt yet.")
            self.assertIn("Hidden", data["dealerHand"])

    def test_game_status_shows_soft_total_display(self):
        with self.client as client:
            with client.session_transaction() as session:
                session["game_state"] = {
                    "player": {
                        "name": "Player 1",
                        "hand": [
                            {"rank": "A", "suit": "Hearts"},
                            {"rank": "6", "suit": "Clubs"},
                        ],
                        "hands": [[
                            {"rank": "A", "suit": "Hearts"},
                            {"rank": "6", "suit": "Clubs"},
                        ]],
                        "hand_bets": [25],
                        "active_hand_index": 0,
                        "bankroll": 1000,
                        "current_bet": 25,
                    },
                    "dealer": {
                        "name": "Dealer",
                        "hand": [
                            {"rank": "5", "suit": "Spades"},
                            {"rank": "K", "suit": "Diamonds"},
                        ],
                        "hands": [[
                            {"rank": "5", "suit": "Spades"},
                            {"rank": "K", "suit": "Diamonds"},
                        ]],
                        "hand_bets": [0],
                        "active_hand_index": 0,
                        "bankroll": 1000,
                        "current_bet": 0,
                    },
                    "awaiting_bet": False,
                    "round_complete": False,
                    "last_result": "",
                }
            response = client.get("/blackjack/game_status")
            html = response.get_data(as_text=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn("7 / 17", html)

    def test_cannot_place_bet_during_active_round(self):
        with self.client as client:
            self._start_active_round(client, bet=25)
            response = client.post("/blackjack/bet", json={"bet": 10})
            self.assertEqual(response.status_code, 400)
            self.assertIn("Finish the current hand", response.get_json()["error"])

    def test_game_status(self):
        with self.client as client:
            client.post("/blackjack/start")
            client.post("/blackjack/bet", json={"bet": 15})
            response = client.get("/blackjack/game_status")
            self.assertEqual(response.status_code, 200)
            page = response.get_data(as_text=True)
            self.assertIn("Dealer Hand", page)
            self.assertIn("Table Status", page)

    def test_handle_action_requires_bet_first(self):
        with self.client as client:
            client.post("/blackjack/start")
            response = client.post("/blackjack/action/hit")
            self.assertEqual(response.status_code, 400)
            self.assertIn("Place a bet", response.get_json()["error"])

    def test_handle_hit_action(self):
        with self.client as client:
            self._start_active_round(client, bet=20)
            response = client.post("/blackjack/action/hit")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn("playerHand", data)
            self.assertFalse(data["canDoubleDown"])

    def test_invalid_action(self):
        with self.client as client:
            self._start_active_round(client, bet=20)
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

    def test_devtools_options_available_in_testing(self):
        response = self.client.get("/blackjack/devtools/options")
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["enabled"])
        self.assertTrue(any(scenario["name"] == "split_eights" for scenario in data["scenarios"]))

    def test_devtools_seed_applies_manual_round_state(self):
        response = self.client.post(
            "/blackjack/devtools/seed",
            json={
                "player": "8-Clubs,8-Diamonds",
                "dealer": "6-Hearts,Q-Spades",
                "deck": "3-Clubs,K-Hearts,2-Diamonds",
                "bet": 50,
                "bankroll": 1200,
            },
        )
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["bankroll"], 1200)
        self.assertEqual(data["currentBet"], 50)
        self.assertEqual(len(data["game"]["player"]["hands"]), 1)
        self.assertEqual(data["game"]["dealer"]["hand"][0]["rank"], "6")


if __name__ == "__main__":
    unittest.main()
