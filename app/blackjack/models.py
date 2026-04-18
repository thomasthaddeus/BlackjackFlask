"""blackjack/models.py

This module defines the models for a blackjack game, including the Card, Deck,
Player, Dealer, and Game classes.

Classes:
    Card: Represents a single card in the deck.
    Deck: Represents a deck of cards, providing methods to shuffle and deal
      cards.
    Player: Represents a player in the game, holding their hand, bankroll, and
      current bet.
    Dealer: Inherits from Player, with specific behaviors for the dealer.
    Game: Manages the flow of the game, including dealing cards, managing
      player actions, and determining outcomes.

Functions:
    load_strategy: Loads a blackjack strategy from a CSV file.
    retry_start_new_round: Attempts to start a new round multiple times in case
      of failure.
    handle_empty_deck: Manages the situation when the deck runs out of cards.
    determine_best_move: Determines the best move for the player based on the
      strategy.
    double_down: Checks if the player can double down based on their hand.
    surrender: Checks if the player should surrender based on their hand and
      the dealer's card.
    handle_surrender: Adjusts the player's bankroll when they surrender.
    resolve_bets: Adjusts the player's bankroll based on the result of the
      round.

Returns:
    Various types based on the functions, primarily dealing with game state and
      player actions.
"""

import csv
from pathlib import Path
from random import shuffle
from ..utils import calculate_hand_value, assign_value, setup_logging

logger = setup_logging()

class Card:
    """
    Represents a single card in the deck.

    Attributes:
        rank (str): The rank of the card (e.g., '2', '3', 'K', 'A').
        suit (str): The suit of the card (e.g., 'Hearts', 'Diamonds').
        value (int): The value of the card, assigned based on its rank.
    """
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.value = assign_value(rank)

    def __repr__(self):
        return f"{self.rank} of {self.suit}"

    def serialize(self):
        """Return a JSON-serializable card representation."""
        return {"rank": self.rank, "suit": self.suit}

class Deck:
    """
    Represents a deck of cards, providing methods to shuffle and deal cards.

    Attributes:
        suits (list): The four suits in a standard deck of cards.
        ranks (list): The thirteen ranks in a standard deck of cards.
        cards (list): The list of Card objects in the deck.
    """
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

    def __init__(self):
        self.cards = [Card(rank, suit) for suit in self.suits for rank in self.ranks]
        self.shuffle()

    def shuffle(self):
        """Shuffle the deck of cards."""
        shuffle(self.cards)

    def deal(self):
        """Deal a card from the deck.

        Returns:
            Card: The dealt card, or None if the deck is empty.
        """
        if self.cards:
            return self.cards.pop()
        return None

class Player:
    """
    Represents a player in the game, holding their hand, bankroll, and current bet.

    Attributes:
        name (str): The name of the player.
        hand (list): The list of Card objects in the player's hand.
        bankroll (int): The amount of money the player has.
        current_bet (int): The current bet placed by the player.
    """
    def __init__(self, name, starting_bankroll=1000):
        self.name = name
        self.hands = [[]]
        self.hand_bets = [0]
        self.active_hand_index = 0
        self.bankroll = starting_bankroll

    @property
    def hand(self):
        """Return the currently active hand."""
        return self.hands[self.active_hand_index]

    @hand.setter
    def hand(self, value):
        """Replace the currently active hand."""
        self.hands[self.active_hand_index] = value

    @property
    def current_bet(self):
        """Return the bet for the currently active hand."""
        return self.hand_bets[self.active_hand_index]

    @current_bet.setter
    def current_bet(self, amount):
        """Set the bet for the currently active hand."""
        self.hand_bets[self.active_hand_index] = amount

    def reset_for_round(self):
        """Reset all hands and bets for a new round."""
        self.hands = [[]]
        self.hand_bets = [0]
        self.active_hand_index = 0

    def add_card(self, card):
        """Add a card to the player's hand."""
        self.hand.append(card)

    def hand_value(self, hand=None):
        """Calculate the value of the player's hand.

        Returns:
            int: The total value of the hand.
        """
        return calculate_hand_value(hand if hand is not None else self.hand)

    def place_bet(self, amount):
        """Place a bet for the current round.

        Args:
            amount (int): The amount to bet.

        Raises:
            ValueError: If the bet amount is invalid.
        """
        if amount > 0 and amount <= self.bankroll:
            self.current_bet = amount
            logger.info("Placed bet of {amount} on hand {hand_index}", amount=amount, hand_index=self.active_hand_index + 1)
        else:
            raise ValueError("Invalid bet amount")

    def can_split(self):
        """Return whether the current hand can be split into two hands."""
        return (
            len(self.hands) == 1
            and len(self.hand) == 2
            and self.hand[0].rank == self.hand[1].rank
            and self.current_bet > 0
            and (self.current_bet * 2) <= self.bankroll
        )

    def split(self, deck):
        """Split the current hand into two separate hands."""
        if not self.can_split():
            raise ValueError("Cannot split this hand")

        first_card, second_card = self.hand
        split_bet = self.current_bet
        self.hands = [[first_card], [second_card]]
        self.hand_bets = [split_bet, split_bet]
        self.active_hand_index = 0
        self.hands[0].append(deck.deal())
        self.hands[1].append(deck.deal())
        logger.info("Split hand into two hands with bet {bet}", bet=split_bet)

    def advance_hand(self):
        """Move to the next hand if one exists."""
        if self.active_hand_index < len(self.hands) - 1:
            self.active_hand_index += 1
            return True
        return False

    def adjust_bankroll(self, result):
        """Adjust the player's bankroll based on the result of the round.

        Args:
            result (str): The result of the round ('win', 'lose', 'surrender').
        """
        if result == "win":
            self.bankroll += self.current_bet
        elif result == "lose":
            self.bankroll -= self.current_bet
        elif result == "surrender":
            self.bankroll -= self.current_bet / 2

    def serialize(self):
        """Return a JSON-serializable player representation."""
        return {
            "name": self.name,
            "hand": [card.serialize() for card in self.hand],
            "hands": [
                [card.serialize() for card in hand]
                for hand in self.hands
            ],
            "hand_bets": self.hand_bets,
            "active_hand_index": self.active_hand_index,
            "bankroll": self.bankroll,
            "current_bet": self.current_bet,
        }

class Dealer(Player):
    """
    Inherits from Player, with specific behaviors for the dealer.

    Methods:
        play: The dealer's actions during their turn.
    """
    def __init__(self):
        super().__init__("Dealer")

    def play(self, deck):
        """The dealer's actions during their turn.

        Args:
            deck (Deck): The deck of cards used in the game.
        """
        while self.hand_value() < 17:
            self.add_card(deck.deal())

class Game:
    """
    Manages the flow of the game, including dealing cards, managing player actions, and determining outcomes.

    Attributes:
        deck (Deck): The deck of cards used in the game.
        player (Player): The player in the game.
        dealer (Dealer): The dealer in the game.
        strategy (dict): The blackjack strategy loaded from a CSV file.
        used_cards (list): The list of used cards in the game.
    """
    def __init__(self):
        self.deck = Deck()
        self.player = Player("Player 1")
        self.dealer = Dealer()
        strategy_path = Path(__file__).resolve().parents[1] / "data" / "blackjack_strategy.csv"
        self.strategy = self.load_strategy(strategy_path)
        self.used_cards = []
        self.awaiting_bet = True
        self.round_complete = False
        self.last_result = ""

    def load_strategy(self, filename):
        """
        Load blackjack strategy from a CSV file into a dictionary.

        Args:
            filename (str): Path to the CSV file containing the strategy.

        Returns:
            dict: Dictionary with player hands as keys and sub-dictionaries as values,
                where each sub-dictionary maps dealer's card to an action.
        """
        strategy = {}
        logger.info("Loading blackjack strategy from {filename}", filename=filename)
        with open(filename, mode="r", encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            headers = next(reader)[1:]  # Skip the first header for 'my_hand'

            for row in reader:
                hand = row[0]  # Player's hand (e.g., '8', '9', 'a2', 'd2')
                actions = row[1:]
                strategy[hand] = dict(zip(headers, actions))

        return strategy

    @staticmethod
    def _deserialize_card(card_data):
        """Build a card instance from serialized data."""
        return Card(card_data["rank"], card_data["suit"])

    @classmethod
    def from_dict(cls, data):
        """Restore a game instance from JSON-serializable session data."""
        game = cls()
        game.deck.cards = [
            cls._deserialize_card(card_data)
            for card_data in data.get("deck", [])
        ]
        player_data = data.get("player", {})
        serialized_hands = player_data.get("hands")
        if serialized_hands:
            game.player.hands = [
                [cls._deserialize_card(card_data) for card_data in hand]
                for hand in serialized_hands
            ]
        else:
            game.player.hands = [[
                cls._deserialize_card(card_data)
                for card_data in player_data.get("hand", [])
            ]]
        game.player.hand_bets = player_data.get(
            "hand_bets",
            [player_data.get("current_bet", 0)] * len(game.player.hands),
        )
        game.player.active_hand_index = player_data.get("active_hand_index", 0)
        game.player.bankroll = player_data.get("bankroll", 1000)
        game.dealer.hand = [
            cls._deserialize_card(card_data)
            for card_data in data.get("dealer", {}).get("hand", [])
        ]
        game.used_cards = [
            cls._deserialize_card(card_data)
            for card_data in data.get("used_cards", [])
        ]
        game.awaiting_bet = data.get("awaiting_bet", True)
        game.round_complete = data.get("round_complete", False)
        game.last_result = data.get("last_result", "")
        return game

    def serialize(self):
        """Return a JSON-serializable game representation."""
        return {
            "player": self.player.serialize(),
            "dealer": self.dealer.serialize(),
            "deck": [card.serialize() for card in self.deck.cards],
            "used_cards": [card.serialize() for card in self.used_cards],
            "awaiting_bet": self.awaiting_bet,
            "round_complete": self.round_complete,
            "last_result": self.last_result,
        }

    def reset_for_new_game(self):
        """Reset the round while preserving the player's bankroll."""
        logger.info("Resetting game while preserving bankroll {bankroll}", bankroll=self.player.bankroll)
        self.deck = Deck()
        self.player.reset_for_round()
        self.dealer.hand = []
        self.used_cards = []
        self.awaiting_bet = True
        self.round_complete = False
        self.last_result = ""

    def start_new_round(self):
        """Start a new round of the game."""
        try:
            logger.info("Starting new round with bankroll {bankroll}", bankroll=self.player.bankroll)
            self.deck = Deck()  # Reinitialize deck each round
            self.player.reset_for_round()
            self.dealer.hand = []
            self.used_cards = []
            self.awaiting_bet = False
            self.round_complete = False
            self.last_result = ""
            self.deal_initial_cards()
        except ValueError as e:  # Assuming ValueError is raised from Deck on issues
            logger.error("Failed to start a new round: %s", e)
            self.retry_start_new_round()
        except Exception as e:
            logger.critical("Unexpected error starting a new round: %s", e)
            raise  # Re-raise to handle or log at a higher level

    def retry_start_new_round(self, attempts=3):
        """Attempt to start a new round up to a specified number of times.

        Args:
            attempts (int): The number of attempts to retry.
        """
        for attempt in range(1, attempts + 1):
            try:
                self.deck = Deck()  # Reinitialize deck each round
                self.player.reset_for_round()
                self.dealer.hand = []
                self.used_cards = []
                self.awaiting_bet = False
                self.round_complete = False
                self.last_result = ""
                self.deal_initial_cards()
                break  # Break out of loop if successful
            except ValueError as e:
                if attempt == attempts:
                    logger.error("All retries failed. Unable to start a new round: %s", e)
                    raise ValueError("Failed to start new round after retries") from e
                logger.warning("Retrying start of new round (%s/%s): %s", attempt, attempts, e)

    def deal_initial_cards(self):
        """Deal initial cards to both player and dealer."""
        for _ in range(2):  # Dealing two cards each to start
            self.player.add_card(self.deck.deal())
            self.dealer.add_card(self.deck.deal())
        logger.debug(
            "Initial cards dealt. Player hand: {player_hand}. Dealer up card: {dealer_card}",
            player_hand=self.player.hand,
            dealer_card=self.dealer.hand[0] if self.dealer.hand else None,
        )

    def _advance_or_resolve(self):
        """Advance to the next player hand or finish the round."""
        if self.player.advance_hand():
            logger.info("Advanced to player hand {hand_index}", hand_index=self.player.active_hand_index + 1)
            return False
        self.dealer_play()
        self.end_round()
        return True

    def player_turn(self):
        """Manage the player's turn based on the strategy."""
        dealer_card = self.dealer.hand[0] if self.dealer.hand else None
        if dealer_card:
            action = self.determine_best_move(self.player.hand, dealer_card)
            while action != "stand":
                try:
                    if action == "hit":
                        self.player.add_card(self.deck.deal())
                    elif action == "Double Down":
                        if self.double_down(self.player.hand):
                            self.player.add_card(self.deck.deal())
                            break  # End turn after double down
                    elif action == "Surrender":
                        self.handle_surrender()
                        return
                except ValueError as e:
                    logger.error("Game Error: %s", e)
                    break  # Stop the game or handle the empty deck situation
                action = self.determine_best_move(self.player.hand, dealer_card)

    def dealer_play(self):
        """Manage the dealer's turn."""
        try:
            while self.dealer.hand_value() < 17:
                self.dealer.add_card(self.deck.deal())
        except ValueError as e:
            logger.error("Game Error: %s", e)  # Log the error
            self.handle_empty_deck()  # Call a method to manage the situation

    def handle_empty_deck(self):
        """Handle the situation when the deck is empty."""
        # Option 1: Re-shuffle the deck
        if len(self.used_cards) > 0:
            self.deck.cards = self.used_cards
            self.deck.shuffle()
            logger.info("Deck was empty. Reshuffled the used cards into the deck.")
        else:
            # Option 2: End the round and possibly the game if no cards are left
            logger.info("No cards left to continue the game.")
            self.end_round()
            # Consider signaling game over or resetting the game state

    def determine_best_move(self, player_hand, dealer_card):
        """Determine the best move based on the loaded blackjack strategy.

        Args:
            player_hand (list): The player's current hand.
            dealer_card (Card): The dealer's visible card.

        Returns:
            str: The best move ('hit', 'stand', 'Double Down', 'Surrender').
        """
        player_value = calculate_hand_value(player_hand)
        soft_hand = any(card.rank == "A" for card in player_hand)
        hand_key = (
            f"a{player_value - 11}"
            if soft_hand and player_value > 21
            else str(player_value)
        )

        dealer_rank = dealer_card.rank
        dealer_rank = "T" if dealer_rank in ["J", "Q", "K"] else dealer_card.rank
        move = self.strategy.get(hand_key, {}).get(dealer_rank, "H")

        # Interpretation of moves when multiple options are given, e.g., 'DH' or 'RH'
        if "D" in move and self.double_down(player_hand):
            move = "Double Down"
        elif "R" in move and self.surrender(player_hand, dealer_card):
            move = "Surrender"
        elif "D" in move or "R" in move:  # Handle cases where double down or surrender is not possible
            move = "Hit"  # Default to 'Hit' if double down or surrender not possible
        elif move == "S":
            move = "Stand"
        elif move == "H":
            move = "Hit"

        return move

    def double_down(self, hand):
        """Determine if the player can double down based on their hand.

        Args:
            hand (list): The player's current hand.

        Returns:
            bool: True if the player can double down, False otherwise.
        """
        total = calculate_hand_value(hand)
        has_ace = any(card.rank == "A" for card in hand)

        # Total 9, 10, or 11 without an ace
        if total in [9, 10, 11] and not has_ace:
            return True
        # Total 16, 17, or 18 with an ace
        elif total in [16, 17, 18] and has_ace:
            return True
        return False

    def surrender(self, plyr_hand, dealer_card):
        """Determine if the player can surrender based on their hand and the dealer's card.

        Args:
            plyr_hand (list): The player's current hand.
            dealer_card (Card): The dealer's visible card.

        Returns:
            bool: True if the player should surrender, False otherwise.
        """
        player_value = calculate_hand_value(plyr_hand)
        dealer_rank = (
            dealer_card.rank if dealer_card.rank not in ["J", "Q", "K"] else "10"
        )

        # Convert ace to '10' if needed for simplicity
        if dealer_rank == "A":
            dealer_rank = "10"

        # Check if the player's hand meets the criteria for surrendering
        if player_value == 16 and dealer_rank in ["9", "10", "A"]:
            # Ensure not to surrender if the hand consists of two 8s (split is preferable)
            if len(plyr_hand) == 2 and all(card.rank == "8" for card in plyr_hand):
                return False
            return True
        elif player_value == 15 and dealer_rank == "10":
            return True

        return False

    def end_round(self):
        """End the current round and determine the outcome."""
        dealer_score = self.dealer.hand_value()
        results = []
        for hand in self.player.hands:
            player_score = self.player.hand_value(hand)
            result = "draw"
            if player_score > 21 or (dealer_score <= 21 and dealer_score > player_score):
                result = "lose"
            elif dealer_score > 21 or player_score > dealer_score:
                result = "win"
            results.append(result)
        self.round_complete = True
        self.awaiting_bet = True
        self.last_result = ", ".join(
            f"Hand {index + 1}: {result}"
            for index, result in enumerate(results)
        )
        logger.info(
            "Round complete. Dealer score {dealer_score}. Results: {results}",
            dealer_score=dealer_score,
            results=self.last_result,
        )
        self.resolve_bets(results)

    def handle_surrender(self):
        """Adjust the player's bankroll when they surrender."""
        self.round_complete = True
        self.awaiting_bet = True
        self.last_result = "Surrender"
        logger.info("Player surrendered hand {hand_index}", hand_index=self.player.active_hand_index + 1)
        self.player.adjust_bankroll("surrender")

    def resolve_bets(self, result):
        """Adjust the player's bankroll based on the result of the round.

        Args:
            result (str | list[str]): The result or results of the round.
        """
        if isinstance(result, list):
            active_index = self.player.active_hand_index
            for index, hand_result in enumerate(result):
                self.player.active_hand_index = index
                self.player.adjust_bankroll(hand_result)
            self.player.active_hand_index = active_index
            return
        self.player.adjust_bankroll(result)
