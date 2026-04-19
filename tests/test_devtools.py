"""Tests for the developer tools harness."""

import unittest

from app.tools.devtools import BlackjackDevTools
from app.tools.devtools_core import parse_card, parse_cards


class TestDevTools(unittest.TestCase):
    """Verify deterministic devtools helpers."""

    def setUp(self):
        self.tools = BlackjackDevTools(log_level="ERROR")

    def test_parse_card_supports_short_and_long_suits(self):
        ace = parse_card("A-Hearts")
        ten = parse_card("10-s")
        self.assertEqual((ace.rank, ace.suit), ("A", "Hearts"))
        self.assertEqual((ten.rank, ten.suit), ("10", "Spades"))

    def test_seed_round_exposes_controlled_snapshot(self):
        snapshot = self.tools.seed_round(
            player_cards=parse_cards("8-Clubs,8-Diamonds"),
            dealer_cards=parse_cards("6-Hearts,Q-Spades"),
            deck_cards=parse_cards("3-Clubs,K-Hearts"),
            bet=50,
            bankroll=1200,
        )
        self.assertEqual(snapshot["bankroll"], 1200)
        self.assertEqual(snapshot["current_bet"], 50)
        self.assertEqual(snapshot["player_hands"][0], ["8 of Clubs", "8 of Diamonds"])
        self.assertEqual(snapshot["dealer_hand"], ["6 of Hearts", "Q of Spades"])
        self.assertEqual(snapshot["deck_depth"], 2)

    def test_apply_scenario_and_run_action_sequence(self):
        self.tools.apply_scenario("soft_ace")
        result = self.tools.action("hit")
        self.assertEqual(result["status_code"], 200)
        payload = result["payload"]
        self.assertIn("playerHands", payload)
        self.assertIn("strategyAdvice", payload)


if __name__ == "__main__":
    unittest.main()
