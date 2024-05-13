import unittest
from unittest.mock import MagicMock
from app.blackjack.models import Card, Deck, Player, Dealer, Game

class TestCard(unittest.TestCase):
    def test_card_value(self):
        """Test card values, including face cards and aces."""
        ace = Card('A', 'Hearts')
        king = Card('K', 'Hearts')
        three = Card('3', 'Hearts')
        self.assertEqual(ace.value, 11)
        self.assertEqual(king.value, 10)
        self.assertEqual(three.value, 3)

class TestDeck(unittest.TestCase):
    def test_deck_length(self):
        """Test that a new deck has 52 cards."""
        deck = Deck()
        self.assertEqual(len(deck.cards), 52)

    def test_shuffle_deck(self):
        """Test that shuffle changes the order of the cards."""
        deck = Deck()
        original_order = deck.cards[:]
        deck.shuffle()
        self.assertNotEqual(original_order, deck.cards)

    def test_deal_card(self):
        """Test dealing a card reduces the deck size."""
        deck = Deck()
        deck.deal()
        self.assertEqual(len(deck.cards), 51)

class TestPlayer(unittest.TestCase):
    def test_add_card(self):
        """Test adding a card to the player's hand."""
        player = Player("Test Player")
        card = Card('5', 'Diamonds')
        player.add_card(card)
        self.assertIn(card, player.hand)

    def test_hand_value(self):
        """Test the calculation of hand value, accounting for aces."""
        player = Player("Test Player")
        cards = [Card('A', 'Diamonds'), Card('K', 'Hearts')]
        for card in cards:
            player.add_card(card)
        self.assertEqual(player.hand_value(), 21)

class TestDealer(unittest.TestCase):
    def test_dealer_play(self):
        """Test dealer plays correctly (stops at 17 or higher)."""
        deck = Deck()
        dealer = Dealer()
        dealer.play(deck)
        self.assertTrue(dealer.hand_value() >= 17)

class TestGame(unittest.TestCase):
    def setUp(self):
        """Set up a game instance before each test."""
        self.game = Game()

    def test_start_new_round(self):
        """Test starting a new round resets hands and deck."""
        self.game.start_new_round()
        self.assertEqual(len(self.game.player.hand), 0)
        self.assertEqual(len(self.game.dealer.hand), 0)
        self.assertEqual(len(self.game.deck.cards), 52)

    def test_player_turn(self):
        """Test player actions during their turn."""
        self.game.dealer.hand = [Card('9', 'Hearts')]  # Dealer shows a 9
        self.game.player.hand = [Card('6', 'Clubs'), Card('5', 'Diamonds')]
        self.game.player_turn()
        # Assuming default strategy would hit in this scenario:
        self.assertTrue(len(self.game.player.hand) >= 3)

    def test_determine_best_move(self):
        """Test the strategy decision making."""
        self.game.dealer.hand = [Card('10', 'Spades')]
        self.game.player.hand = [Card('6', 'Clubs'), Card('5', 'Diamonds')]
        move = self.game.determine_best_move(self.game.player.hand, self.game.dealer.hand[0])
        self.assertEqual(move, 'Hit')  # Example expected strategy

if __name__ == '__main__':
    unittest.main()
