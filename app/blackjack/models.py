"""blackjack/models.py
_summary_

_extended_summary_

Returns:
    _type_: _description_
"""

from flask import session
from utils import (
    get_card_value,
    calculate_hand_value,
    determine_best_move,
    shuffle_deck,
    setup_logging,
    save_game_state,
    load_game_state,
    load_strategy,
)


class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.value = self.assign_value(rank)

    def assign_value(self, rank):
        if rank in ["J", "Q", "K"]:
            return 10
        elif rank == "A":
            return 11
        return int(rank)

    def __repr__(self):
        return f"{self.rank} of {self.suit}"


class Deck:
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

    def __init__(self):
        self.cards = [Card(rank, suit) for suit in self.suits for rank in self.ranks]
        self.shuffle()

    def shuffle(self):
        shuffle_deck(self.cards)

    def deal(self):
        return self.cards.pop()


class Player:
    def __init__(self, name, starting_bankroll=1000):
        self.name = name
        self.hand = []
        self.bankroll = starting_bankroll

    def add_card(self, card):
        try:
            self.hand.append(card)
            self.adjust_for_aces()
        except Exception as e:
            print(
                f"Error adding card to hand: {e}"
            )  # Log error or handle it appropriately

    def hand_value(self):
        return calculate_hand_value(self.hand)

    def adjust_for_aces(self):
        self.value = calculate_hand_value(self.hand)

    def hit(self, deck, hand):
        hand.add_card(deck.deal())
        hand.adjust_for_ace()

    def take_bet(self):
        bet = session.get("bet", 0)
        chips = session.get("total_chips", 100)  # Default to 100 if not set
        if bet > chips:
            return False, f"Sorry, your bet cannot exceed {chips}"
        session["total_chips"] -= bet
        return True, ""

    def hit_or_stand(self, deck, hand, action):
        if action == "h":
            self.hit(deck, hand)
        elif action == "s":
            return "stand"
        return "continue"


class Dealer(Player):
    def __init__(self):
        super().__init__("Dealer")

    def play(self, deck):
        while self.hand_value() < 17:
            self.add_card(deck.deal())


class Game:
    def __init__(self):
        self.deck = Deck()
        self.player = Player("Player 1")
        self.dealer = Dealer()
        self.strategy = load_strategy("../data/blackjack_strategy.csv")

    def start_new_round(self):
        try:
            self.deck = Deck()  # Reinitialize deck each round
            self.player.hand = []
            self.dealer.hand = []
        except Exception as e:
            print(f"Error starting a new round: {e}")
            # Consider additional handling like retrying the round start or logging

    def player_turn(self):
        try:
            action = get_action(
                self.strategy, str(self.player.hand_value()), self.dealer.hand[0].rank
            )
            while action != "stand":
                if action == "hit":
                    self.player.add_card(self.deck.deal())
                action = get_action(
                    self.strategy,
                    str(self.player.hand_value()),
                    self.dealer.hand[0].rank,
                )
        except Exception as e:
            print(f"Error during player's turn: {e}")


def get_action(strategy, player_hand, dealer_card):
    """
    Get the recommended action from the strategy.

    :param strategy: Loaded strategy dictionary.
    :param player_hand: The hand of the player (as a string, e.g., '8', 'a2').
    :param dealer_card: The card the dealer shows (as a string, '2'-'A').
    :return: Recommended action as a string.
    """
    return strategy.get(player_hand, {}).get(dealer_card, "Unknown")
