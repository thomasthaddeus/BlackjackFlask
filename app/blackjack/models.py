"""blackjack/models.py
_summary_

_extended_summary_

Returns:
    _type_: _description_
"""

import csv
from random import shuffle
from ..utils import (
    get_card_value,
    calculate_hand_value,
)


class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.value = get_card_value(self)

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

    def shuffle_deck(self, deck):
        """Shuffle the deck of cards."""
        shuffle(deck)
        return deck

    def shuffle(self):
        self.shuffle_deck(self.cards)

    def deal(self):
        if self.cards:
            return self.cards.pop()
        return None


class Player:
    def __init__(self, name, starting_bankroll=1000):
        self.name = name
        self.hand = []
        self.bankroll = starting_bankroll

    def add_card(self, card):
        self.hand.append(card)

    def hand_value(self):
        return calculate_hand_value(self.hand)

    def load_strategy(self, filename):
        """
        Load blackjack strategy from a CSV file into a dictionary.

        :param filename: Path to the CSV file containing the strategy.
        :return: Dictionary with player hands as keys and sub-dictionaries as
          values, where each sub-dictionary maps dealer's card to an action.
        """
        strategy = {}
        with open(filename, mode="r", encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            headers = next(reader)[1:]  # Skip the first header for 'my_hand'

            for row in reader:
                hand = row[0]  # Player's hand (e.g., '8', '9', 'a2', 'd2')
                actions = row[1:]
                strategy[hand] = dict(zip(headers, actions))

        return strategy


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
        self.strategy = Player.load_strategy(self, "../data/blackjack_strategy.csv")

    def start_new_round(self):
        try:
            self.deck = Deck()  # Reinitialize deck each round
            self.player.hand = []
            self.dealer.hand = []
        except Exception as e:
            print(f"Error starting a new round: {e}")

            # Consider additional handling like retrying the round start or logging

    def player_turn(self):
        dealer_card = self.dealer.hand[0] if self.dealer.hand else None
        if dealer_card:
            action = self.determine_best_move(self.player.hand, dealer_card)
            while action != "stand":
                if action == "hit":
                    self.player.add_card(self.deck.deal())
                elif action == "Double Down" and self.double_down(self.player.hand):
                    self.player.add_card(self.deck.deal())
                    break  # End turn after double down
                elif action == "Surrender":
                    # return half the players bet
                    # end hand for player
                    break
                action = self.determine_best_move(self.player.hand, dealer_card)

    def determine_best_move(self, player_hand, dealer_card):
        """Determine the best move based on the loaded blackjack strategy."""
        player_value = calculate_hand_value(player_hand)
        soft_hand = any(card.rank == "A" for card in player_hand)
        hand_key = (
            f"a{player_value - 11}"
            if soft_hand and player_value > 21
            else str(player_value)
        )

        dealer_rank = dealer_card.rank
        dealer_rank = "T" if dealer_rank in ["J", "Q", "K"] else dealer_rank

        move = self.strategy.get(hand_key, {}).get(
            dealer_rank, "H"
        )  # Default to 'Hit' if no strategy found

        # Interpretation of moves when multiple options are given, e.g., 'DH' or 'RH'
        if "D" in move and self.double_down(player_hand):
            move = "Double Down"
        elif "R" in move and self.surrender(player_hand, dealer_card):
            move = "Surrender"
        elif (
            "D" in move or "R" in move
        ):  # Handle cases where double down or surrender is not possible
            move = "Hit"  # Default to 'Hit' if double down or surrender not possible
        elif move == "S":
            move = "Stand"
        elif move == "H":
            move = "Hit"

        return move

    def double_down(self, hand):
        """Determine if the player can double down based on their hand."""
        total = calculate_hand_value(hand)
        has_ace = any(card.rank == "A" for card in hand)

        # Total 9, 10, or 11 without an ace
        if total in [9, 10, 11] and not has_ace:
            return True
        # Total 16, 17, or 18 with an ace
        elif total in [16, 17, 18] and has_ace:
            return True
        return False

    def surrender(self, player_hand, dealer_card):
        """Determine if the player can surrender based on their hand and the dealer's card."""
        player_value = calculate_hand_value(player_hand)
        dealer_rank = (
            dealer_card.rank if dealer_card.rank not in ["J", "Q", "K"] else "10"
        )

        # Convert ace to '10' if needed for simplicity
        if dealer_rank == "A":
            dealer_rank = "10"

        # Check if the player's hand meets the criteria for surrendering
        if player_value == 16 and dealer_rank in ["9", "10", "A"]:
            # Ensure not to surrender if the hand consists of two 8s (split is preferable)
            if len(player_hand) == 2 and all(card.rank == "8" for card in player_hand):
                return False
            return True
        elif player_value == 15 and dealer_rank == "10":
            return True

        return False
