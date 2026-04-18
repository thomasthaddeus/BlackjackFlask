"""Game logic tests for blackjack models."""

import unittest

from app.blackjack.models import Card, Deck, Player, Dealer, Game


class TestCard(unittest.TestCase):
    """Verify card value behavior."""

    def test_card_value(self):
        ace = Card("A", "Hearts")
        king = Card("K", "Hearts")
        three = Card("3", "Hearts")
        self.assertEqual(ace.value, 11)
        self.assertEqual(king.value, 10)
        self.assertEqual(three.value, 3)


class TestDeck(unittest.TestCase):
    """Verify deck behavior."""

    def test_deck_length(self):
        deck = Deck()
        self.assertEqual(len(deck.cards), 52)

    def test_deal_card(self):
        deck = Deck()
        dealt = deck.deal()
        self.assertIsNotNone(dealt)
        self.assertEqual(len(deck.cards), 51)


class TestPlayer(unittest.TestCase):
    """Verify player helpers and split support."""

    def test_hand_value_with_ace_adjustment(self):
        player = Player("Test Player")
        player.add_card(Card("A", "Diamonds"))
        player.add_card(Card("K", "Hearts"))
        self.assertEqual(player.hand_value(), 21)

    def test_can_split_requires_matching_ranks_and_bet(self):
        player = Player("Test Player")
        player.hand = [Card("8", "Clubs"), Card("8", "Diamonds")]
        player.current_bet = 25
        self.assertTrue(player.can_split())

    def test_split_creates_two_hands(self):
        player = Player("Test Player")
        player.hand = [Card("8", "Clubs"), Card("8", "Diamonds")]
        player.current_bet = 25
        deck = Deck()
        deck.cards = [Card("5", "Spades"), Card("9", "Hearts")] + deck.cards
        player.split(deck)
        self.assertEqual(len(player.hands), 2)
        self.assertEqual(player.hand_bets, [25, 25])
        self.assertEqual(len(player.hands[0]), 2)
        self.assertEqual(len(player.hands[1]), 2)


class TestDealer(unittest.TestCase):
    """Verify dealer turn behavior."""

    def test_dealer_play(self):
        deck = Deck()
        dealer = Dealer()
        dealer.play(deck)
        self.assertGreaterEqual(dealer.hand_value(), 17)


class TestGame(unittest.TestCase):
    """Verify round lifecycle and serialization."""

    def setUp(self):
        self.game = Game()

    def test_start_new_round_deals_cards_and_clears_waiting_flag(self):
        self.game.start_new_round()
        self.assertEqual(len(self.game.player.hand), 2)
        self.assertEqual(len(self.game.dealer.hand), 2)
        self.assertFalse(self.game.awaiting_bet)
        self.assertFalse(self.game.round_complete)

    def test_reset_for_new_game_preserves_bankroll(self):
        self.game.player.bankroll = 875
        self.game.start_new_round()
        self.game.reset_for_new_game()
        self.assertEqual(self.game.player.bankroll, 875)
        self.assertTrue(self.game.awaiting_bet)
        self.assertEqual(self.game.player.hands, [[]])
        self.assertEqual(self.game.dealer.hand, [])

    def test_determine_best_move(self):
        self.game.dealer.hand = [Card("10", "Spades")]
        self.game.player.hand = [Card("6", "Clubs"), Card("5", "Diamonds")]
        move = self.game.determine_best_move(
            self.game.player.hand, self.game.dealer.hand[0]
        )
        self.assertEqual(move, "Hit")

    def test_serialize_round_trip(self):
        self.game.start_new_round()
        self.game.player.bankroll = 930
        payload = self.game.serialize()
        restored = Game.from_dict(payload)
        self.assertEqual(restored.player.bankroll, 930)
        self.assertEqual(len(restored.player.hand), 2)
        self.assertEqual(len(restored.dealer.hand), 2)
        self.assertEqual(restored.awaiting_bet, self.game.awaiting_bet)


if __name__ == "__main__":
    unittest.main()
