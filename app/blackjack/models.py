"""Core blackjack models and turn management."""

from __future__ import annotations

import csv
from pathlib import Path
from random import shuffle

from ..utils import assign_value, calculate_hand_value, format_hand_value, setup_logging


logger = setup_logging("models")


class Card:
    """Represents a single playing card."""

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
    """Represents a shuffled shoe of one or more standard decks."""

    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

    def __init__(self, num_decks=1):
        self.num_decks = num_decks
        self.cards = [
            Card(rank, suit)
            for _ in range(num_decks)
            for suit in self.suits
            for rank in self.ranks
        ]
        self.shuffle()

    def shuffle(self):
        """Shuffle the shoe."""
        shuffle(self.cards)

    def deal(self):
        """Deal the next card from the shoe."""
        if not self.cards:
            return None
        return self.cards.pop()

    def remaining(self):
        """Return the number of cards left in the shoe."""
        return len(self.cards)


class Player:
    """Represents one occupied betting seat at the table."""

    def __init__(self, name, starting_bankroll=1000, table_position=3):
        self.name = name
        self.table_position = table_position
        self.bankroll = starting_bankroll
        self.reset_for_round()

    @property
    def hand(self):
        return self.hands[self.active_hand_index]

    @hand.setter
    def hand(self, value):
        self.hands[self.active_hand_index] = value

    @property
    def current_bet(self):
        return self.hand_bets[self.active_hand_index]

    @current_bet.setter
    def current_bet(self, amount):
        self.hand_bets[self.active_hand_index] = amount

    @property
    def current_state(self):
        return self.hand_states[self.active_hand_index]

    @property
    def current_result(self):
        return self.hand_results[self.active_hand_index]

    def reset_for_round(self):
        """Reset the seat for a new round."""
        self.hands = [[]]
        self.hand_bets = [0]
        self.hand_states = ["playing"]
        self.hand_results = [None]
        self.hand_settled = [False]
        self.active_hand_index = 0

    def add_card(self, card, hand_index=None):
        """Add a card to the active hand or a specific hand."""
        target_index = self.active_hand_index if hand_index is None else hand_index
        self.hands[target_index].append(card)

    def hand_value(self, hand=None):
        """Return the numeric value of a hand."""
        return calculate_hand_value(hand if hand is not None else self.hand)

    def hand_value_display(self, hand=None):
        """Return the display-friendly value of a hand."""
        return format_hand_value(hand if hand is not None else self.hand)

    def place_bet(self, amount):
        """Assign a bet to the active hand."""
        if amount <= 0:
            raise ValueError("Invalid bet amount")
        self.current_bet = amount

    def can_split(self, bankroll=None):
        """Return whether the current hand can be split."""
        additional_bet_allowed = True
        if bankroll is not None:
            additional_bet_allowed = (self.current_bet * 2) <= bankroll
        return (
            len(self.hands) == 1
            and len(self.hand) == 2
            and self.hand[0].rank == self.hand[1].rank
            and self.current_bet > 0
            and additional_bet_allowed
            and self.current_state == "playing"
        )

    def split(self, deck):
        """Split the active hand into two hands."""
        if len(self.hand) != 2 or self.hand[0].rank != self.hand[1].rank:
            raise ValueError("Cannot split this hand")

        first_card, second_card = self.hand
        split_bet = self.current_bet
        self.hands = [[first_card], [second_card]]
        self.hand_bets = [split_bet, split_bet]
        self.hand_states = ["playing", "playing"]
        self.hand_results = [None, None]
        self.hand_settled = [False, False]
        self.active_hand_index = 0
        self.hands[0].append(deck.deal())
        self.hands[1].append(deck.deal())
        logger.info("Split seat {seat} into two hands with bet {bet}", seat=self.name, bet=split_bet)

    def set_hand_state(self, index, state, result=None):
        """Set the state and optionally the result for a hand."""
        self.hand_states[index] = state
        if result is not None:
            self.hand_results[index] = result

    def mark_current_hand(self, state, result=None):
        """Set state/result on the active hand."""
        self.set_hand_state(self.active_hand_index, state, result)

    def select_first_playing_hand(self):
        """Move the cursor to the first hand that can still act."""
        for index, state in enumerate(self.hand_states):
            if state == "playing":
                self.active_hand_index = index
                return True
        return False

    def advance_hand(self):
        """Advance to the next unresolved hand on this seat."""
        for index in range(self.active_hand_index + 1, len(self.hands)):
            if self.hand_states[index] == "playing":
                self.active_hand_index = index
                return True
        return False

    def has_playing_hand(self):
        return any(state == "playing" for state in self.hand_states)

    def has_pending_dealer_resolution(self):
        return any(state == "stood" for state in self.hand_states)

    def is_round_complete(self):
        return not self.has_playing_hand() and not self.has_pending_dealer_resolution()

    def adjust_bankroll(self, result):
        """Retain legacy bankroll adjustment behavior for compatibility."""
        if result == "win":
            self.bankroll += self.current_bet
        elif result == "blackjack":
            self.bankroll += self.current_bet * 1.5
        elif result == "lose":
            self.bankroll -= self.current_bet
        elif result == "surrender":
            self.bankroll -= self.current_bet / 2

    def serialize(self):
        """Return a JSON-serializable seat representation."""
        return {
            "name": self.name,
            "table_position": self.table_position,
            "hand": [card.serialize() for card in self.hand],
            "hands": [[card.serialize() for card in hand] for hand in self.hands],
            "hand_bets": self.hand_bets,
            "hand_states": self.hand_states,
            "hand_results": self.hand_results,
            "hand_settled": self.hand_settled,
            "active_hand_index": self.active_hand_index,
            "bankroll": self.bankroll,
            "current_bet": self.current_bet,
        }


class Dealer(Player):
    """Dealer seat with simple draw rules."""

    def __init__(self):
        super().__init__("Dealer", table_position=-1)

    def play(self, deck):
        while self.hand_value() < 17:
            self.add_card(deck.deal())


class Game:
    """Manage the blackjack table, seats, shoe, and turn order."""

    def __init__(self, seat_count=1, bankroll=1000, shoe_decks=6):
        self.strategy = self.load_strategy(
            Path(__file__).resolve().parents[1] / "data" / "blackjack_strategy.csv"
        )
        self.shoe_decks = shoe_decks
        self.deck = Deck(num_decks=shoe_decks)
        self.used_cards = []
        self.dealer = Dealer()
        self.bankroll = bankroll
        self.seat_count = 0
        self.seats = []
        self.active_seat_index = 0
        self.awaiting_bet = True
        self.round_complete = False
        self.last_result = ""
        self.configure_seats(seat_count)

    @property
    def player(self):
        """Backwards-compatible alias to the currently active seat."""
        if not self.seats:
            self.configure_seats(1)
        return self.seats[self.active_seat_index]

    @staticmethod
    def seat_positions_for_count(count):
        """Map the chosen seat count onto the 7-seat semicircle."""
        layouts = {
            1: [3],
            2: [2, 4],
            3: [2, 3, 4],
            4: [1, 2, 4, 5],
            5: [1, 2, 3, 4, 5],
            6: [0, 1, 2, 4, 5, 6],
            7: [0, 1, 2, 3, 4, 5, 6],
        }
        return layouts.get(count, [3])

    def configure_seats(self, seat_count):
        """Configure how many table spots are occupied by this bankroll."""
        safe_count = max(1, min(7, int(seat_count)))
        positions = self.seat_positions_for_count(safe_count)
        self.seat_count = safe_count
        self.seats = [
            Player(f"P{index + 1}", starting_bankroll=self.bankroll, table_position=position)
            for index, position in enumerate(positions)
        ]
        self.active_seat_index = 0
        logger.info("Configured table for {seat_count} occupied seats.", seat_count=safe_count)

    def load_strategy(self, filename):
        """Load the blackjack strategy table from CSV."""
        strategy = {}
        logger.info("Loading blackjack strategy from {filename}", filename=filename)
        with open(filename, mode="r", encoding="utf-8", newline="") as file:
            reader = csv.reader(file)
            headers = [header.strip("'\"") for header in next(reader)[1:]]
            for row in reader:
                hand = row[0].strip("'\"").lower()
                strategy[hand] = dict(zip(headers, row[1:]))
        return strategy

    @staticmethod
    def _deserialize_card(card_data):
        return Card(card_data["rank"], card_data["suit"])

    @classmethod
    def from_dict(cls, data):
        """Restore a game instance from session data, including legacy payloads."""
        seat_data = data.get("seats")
        if seat_data:
            game = cls(
                seat_count=data.get("seat_count", len(seat_data)),
                bankroll=data.get("bankroll", 1000),
                shoe_decks=data.get("shoe_decks", 6),
            )
            game.seats = []
            for index, serialized_seat in enumerate(seat_data):
                seat = Player(
                    serialized_seat.get("name", f"P{index + 1}"),
                    starting_bankroll=data.get("bankroll", 1000),
                    table_position=serialized_seat.get("table_position", index),
                )
                seat.hands = [
                    [cls._deserialize_card(card_data) for card_data in hand]
                    for hand in serialized_seat.get("hands", [[]])
                ]
                seat.hand_bets = serialized_seat.get("hand_bets", [0] * len(seat.hands))
                seat.hand_states = serialized_seat.get("hand_states", ["playing"] * len(seat.hands))
                seat.hand_results = serialized_seat.get("hand_results", [None] * len(seat.hands))
                seat.hand_settled = serialized_seat.get("hand_settled", [False] * len(seat.hands))
                seat.active_hand_index = serialized_seat.get("active_hand_index", 0)
                game.seats.append(seat)
            game.seat_count = data.get("seat_count", len(game.seats))
            game.active_seat_index = data.get("active_seat_index", 0)
        else:
            player_data = data.get("player", {})
            game = cls(
                seat_count=1,
                bankroll=player_data.get("bankroll", data.get("bankroll", 1000)),
                shoe_decks=data.get("shoe_decks", 6),
            )
            seat = game.seats[0]
            serialized_hands = player_data.get("hands")
            if serialized_hands:
                seat.hands = [
                    [cls._deserialize_card(card_data) for card_data in hand]
                    for hand in serialized_hands
                ]
            else:
                seat.hands = [[cls._deserialize_card(card_data) for card_data in player_data.get("hand", [])]]
            seat.hand_bets = player_data.get("hand_bets", [player_data.get("current_bet", 0)] * len(seat.hands))
            seat.hand_states = player_data.get("hand_states", ["playing"] * len(seat.hands))
            seat.hand_results = player_data.get("hand_results", [None] * len(seat.hands))
            seat.hand_settled = player_data.get("hand_settled", [False] * len(seat.hands))
            seat.active_hand_index = player_data.get("active_hand_index", 0)
            game.active_seat_index = 0

        game.deck = Deck(num_decks=data.get("shoe_decks", 6))
        game.deck.cards = [cls._deserialize_card(card_data) for card_data in data.get("deck", [])]
        game.dealer.hand = [cls._deserialize_card(card_data) for card_data in data.get("dealer", {}).get("hand", [])]
        game.dealer.hand_states = ["playing"]
        game.dealer.hand_results = [None]
        game.dealer.hand_settled = [False]
        game.used_cards = [cls._deserialize_card(card_data) for card_data in data.get("used_cards", [])]
        game.awaiting_bet = data.get("awaiting_bet", True)
        game.round_complete = data.get("round_complete", False)
        game.last_result = data.get("last_result", "")
        game.bankroll = data.get("bankroll", getattr(game, "bankroll", 1000))
        for seat in game.seats:
            seat.bankroll = game.bankroll
        return game

    def serialize(self):
        """Serialize the entire game for the session."""
        if self.seat_count == 1:
            self.bankroll = self.player.bankroll
        return {
            "bankroll": self.bankroll,
            "seat_count": self.seat_count,
            "active_seat_index": self.active_seat_index,
            "shoe_decks": self.shoe_decks,
            "seats": [seat.serialize() for seat in self.seats],
            "player": self.player.serialize(),
            "dealer": self.dealer.serialize(),
            "deck": [card.serialize() for card in self.deck.cards],
            "used_cards": [card.serialize() for card in self.used_cards],
            "awaiting_bet": self.awaiting_bet,
            "round_complete": self.round_complete,
            "last_result": self.last_result,
        }

    def ensure_shoe_capacity(self):
        """Refresh the shoe when it gets too shallow for another full round."""
        minimum_cards = (self.seat_count * 2) + 12
        if self.deck.remaining() < minimum_cards:
            logger.info(
                "Refreshing shoe. Remaining cards {remaining} below threshold {threshold}.",
                remaining=self.deck.remaining(),
                threshold=minimum_cards,
            )
            self.deck = Deck(num_decks=self.shoe_decks)

    def reset_for_new_game(self, seat_count=None):
        """Reset the table while preserving bankroll and the current shoe."""
        if self.seat_count == 1:
            self.bankroll = self.player.bankroll
        if seat_count is not None and int(seat_count) != self.seat_count:
            self.configure_seats(seat_count)
        for seat in self.seats:
            seat.reset_for_round()
        self.dealer.reset_for_round()
        self.active_seat_index = 0
        self.used_cards = []
        self.awaiting_bet = True
        self.round_complete = False
        self.last_result = ""
        logger.info(
            "Reset game while preserving bankroll {bankroll} across {seat_count} seats.",
            bankroll=self.bankroll,
            seat_count=self.seat_count,
        )

    def place_bets(self, amount):
        """Place the same opening bet on every occupied seat."""
        if self.seat_count == 1:
            self.bankroll = self.player.bankroll
        total_bet = amount * self.seat_count
        if amount <= 0 or total_bet > self.bankroll:
            raise ValueError("Invalid bet amount")
        for seat in self.seats:
            seat.reset_for_round()
            seat.place_bet(amount)
            seat.bankroll = self.bankroll

    def start_new_round(self):
        """Start a new round using the persistent shoe."""
        self.ensure_shoe_capacity()
        opening_bets = [seat.current_bet for seat in self.seats]
        for seat in self.seats:
            seat.reset_for_round()
        for index, seat in enumerate(self.seats):
            seat.current_bet = opening_bets[index]
            seat.hand_bets = [opening_bets[index]]
        self.dealer.reset_for_round()
        self.used_cards = []
        self.awaiting_bet = False
        self.round_complete = False
        self.last_result = ""
        self.active_seat_index = 0
        logger.info(
            "Starting new round with bankroll {bankroll} across {seat_count} seats and {cards} cards in shoe.",
            bankroll=self.bankroll,
            seat_count=self.seat_count,
            cards=self.deck.remaining(),
        )
        self.deal_initial_cards()

    def deal_initial_cards(self):
        """Deal two cards to each occupied seat and the dealer."""
        for _ in range(2):
            for seat in self.seats:
                seat.add_card(self.deck.deal())
            self.dealer.add_card(self.deck.deal())
        self.active_seat_index = 0
        self.player.select_first_playing_hand()
        self.check_initial_blackjack()

    def has_blackjack(self, hand):
        return len(hand) == 2 and calculate_hand_value(hand) == 21

    def settle_bet(self, result, bet):
        """Apply a result to the shared bankroll."""
        if result == "win":
            self.bankroll += bet
        elif result == "blackjack":
            self.bankroll += bet * 1.5
        elif result == "lose":
            self.bankroll -= bet
        elif result == "surrender":
            self.bankroll -= bet / 2
        for seat in self.seats:
            seat.bankroll = self.bankroll

    def settle_hand(self, seat, hand_index, result):
        """Settle one seat hand exactly once."""
        if seat.hand_settled[hand_index]:
            return
        seat.hand_results[hand_index] = result
        seat.hand_settled[hand_index] = True
        bet = seat.hand_bets[hand_index]
        self.settle_bet(result, bet)
        seat.hand_states[hand_index] = "resolved"

    def check_initial_blackjack(self):
        """Resolve natural blackjacks on a per-seat basis."""
        dealer_blackjack = self.has_blackjack(self.dealer.hand)
        active_playing_exists = False
        messages = []

        for seat in self.seats:
            if self.has_blackjack(seat.hand):
                if dealer_blackjack:
                    seat.set_hand_state(0, "resolved", "draw")
                    seat.hand_settled[0] = True
                    messages.append(f"{seat.name} Hand 1: push")
                else:
                    seat.set_hand_state(0, "resolved", "blackjack")
                    self.settle_hand(seat, 0, "blackjack")
                    messages.append(f"{seat.name} Hand 1: blackjack")
            elif dealer_blackjack:
                seat.set_hand_state(0, "resolved", "lose")
                self.settle_hand(seat, 0, "lose")
                messages.append(f"{seat.name} Hand 1: lose")
            else:
                active_playing_exists = True

        if dealer_blackjack:
            self.round_complete = True
            self.awaiting_bet = True
            if self.seat_count == 1:
                if self.has_blackjack(self.seats[0].hand):
                    self.last_result = "Push. Both player and dealer have blackjack."
                else:
                    self.last_result = "Dealer blackjack. Hand lost."
            else:
                self.last_result = ", ".join(messages) or "Dealer blackjack."
            logger.info("Dealer natural blackjack resolved all occupied seats.")
            return

        if not active_playing_exists:
            self.round_complete = True
            self.awaiting_bet = True
            if self.seat_count == 1:
                self.last_result = "Blackjack! Player paid 3:2."
            else:
                self.last_result = ", ".join(messages) or "All seats resolved on the opening deal."
            logger.info("Opening deal resolved all seats immediately.")
            return

        self.select_first_playing_seat()

    def select_first_playing_seat(self):
        """Move the cursor to the first seat that can still act."""
        for index, seat in enumerate(self.seats):
            if seat.select_first_playing_hand():
                self.active_seat_index = index
                return True
        return False

    def advance_to_next_playing_position(self):
        """Advance within the current seat first, then across seats."""
        current_seat = self.player
        if current_seat.advance_hand():
            return True
        for index in range(self.active_seat_index + 1, len(self.seats)):
            if self.seats[index].select_first_playing_hand():
                self.active_seat_index = index
                return True
        return False

    def has_pending_dealer_resolution(self):
        return any(seat.has_pending_dealer_resolution() for seat in self.seats)

    def finalize_round_without_dealer(self):
        """Finish the round when all hands were settled before dealer action."""
        self.round_complete = True
        self.awaiting_bet = True
        self.last_result = self._result_summary()

    def _advance_or_resolve(self):
        """Advance to the next actionable hand or resolve the round."""
        if self.advance_to_next_playing_position():
            logger.info(
                "Advanced turn to seat {seat} hand {hand}.",
                seat=self.player.name,
                hand=self.player.active_hand_index + 1,
            )
            return False

        if self.has_pending_dealer_resolution():
            self.dealer_play()
            self.end_round()
            return True

        self.finalize_round_without_dealer()
        return True

    def player_turn(self):
        """Retain a simple autoplay loop for compatibility."""
        dealer_card = self.dealer.hand[0] if self.dealer.hand else None
        while dealer_card and not self.round_complete and self.player.current_state == "playing":
            action = self.determine_best_move(self.player.hand, dealer_card)
            if action == "Hit":
                self.player.add_card(self.deck.deal())
                if self.player.hand_value() > 21:
                    self.player.mark_current_hand("resolved", "lose")
                    self.settle_hand(self.player, self.player.active_hand_index, "lose")
                    break
            elif action == "Double Down":
                self.player.add_card(self.deck.deal())
                if self.player.hand_value() > 21:
                    self.player.mark_current_hand("resolved", "lose")
                    self.settle_hand(self.player, self.player.active_hand_index, "lose")
                else:
                    self.player.mark_current_hand("stood")
                break
            elif action == "Surrender":
                self.handle_surrender()
                return
            else:
                self.player.mark_current_hand("stood")
                break
        self._advance_or_resolve()

    def dealer_play(self):
        """Play out the dealer hand."""
        while self.dealer.hand_value() < 17:
            self.dealer.add_card(self.deck.deal())

    def handle_empty_deck(self):
        """Refresh the shoe if it runs dry."""
        logger.info("Shoe ran empty. Refreshing with a new {shoe_decks}-deck shoe.", shoe_decks=self.shoe_decks)
        self.deck = Deck(num_decks=self.shoe_decks)

    @staticmethod
    def _normalize_rank(rank):
        if rank in ["J", "Q", "K", "10"]:
            return "T"
        return rank

    def _strategy_hand_key(self, player_hand):
        normalized_ranks = [self._normalize_rank(card.rank) for card in player_hand]

        if len(player_hand) == 2 and normalized_ranks[0] == normalized_ranks[1]:
            if normalized_ranks[0] == "A":
                return "aa"
            return f"d{normalized_ranks[0].lower()}"

        if len(player_hand) == 2 and any(card.rank == "A" for card in player_hand):
            non_ace_card = next((card for card in player_hand if card.rank != "A"), None)
            if non_ace_card is not None:
                return f"a{assign_value(non_ace_card.rank)}"

        return str(calculate_hand_value(player_hand))

    def _interpret_strategy_code(self, move_code, player_hand, dealer_card):
        move_code = move_code.strip()
        if move_code in {"Sp", "P", "PH"}:
            return "Split" if self.player.can_split(self.bankroll) else "Hit"
        if move_code == "S":
            return "Stand"
        if move_code == "H":
            return "Hit"
        if move_code == "DH":
            return "Double Down" if self.double_down(player_hand) else "Hit"
        if move_code == "DS":
            return "Double Down" if self.double_down(player_hand) else "Stand"
        if move_code == "RH":
            return "Surrender" if self.surrender(player_hand, dealer_card) else "Hit"
        if move_code == "R":
            return "Surrender" if self.surrender(player_hand, dealer_card) else "Stand"
        return "Hit"

    @staticmethod
    def _fallback_move(player_hand):
        total = calculate_hand_value(player_hand)
        if total >= 17:
            return "Stand"
        return "Hit"

    def determine_best_move(self, player_hand, dealer_card):
        hand_key = self._strategy_hand_key(player_hand)
        dealer_rank = self._normalize_rank(dealer_card.rank)
        move_row = self.strategy.get(hand_key)
        if move_row is None:
            return self._fallback_move(player_hand)
        move_code = move_row.get(dealer_rank)
        if move_code is None:
            return self._fallback_move(player_hand)
        return self._interpret_strategy_code(move_code, player_hand, dealer_card)

    def double_down(self, hand):
        return len(hand) == 2 and self.player.current_state == "playing"

    def surrender(self, player_hand, dealer_card):
        if len(player_hand) != 2 or self.player.current_state != "playing":
            return False
        player_value = calculate_hand_value(player_hand)
        dealer_rank = dealer_card.rank if dealer_card.rank not in ["J", "Q", "K"] else "10"
        if dealer_rank == "A":
            dealer_rank = "10"
        if player_value == 16 and dealer_rank in ["9", "10", "A"]:
            if len(player_hand) == 2 and all(card.rank == "8" for card in player_hand):
                return False
            return True
        return player_value == 15 and dealer_rank == "10"

    def _result_summary(self):
        parts = []
        for seat in self.seats:
            for index, result in enumerate(seat.hand_results):
                if result:
                    label = "push" if result == "draw" else result
                    parts.append(f"{seat.name} Hand {index + 1}: {label}")
        return ", ".join(parts)

    def end_round(self):
        """Resolve all standing hands against the dealer."""
        dealer_score = self.dealer.hand_value()
        for seat in self.seats:
            for index, hand in enumerate(seat.hands):
                if seat.hand_results[index] is not None:
                    continue
                player_score = seat.hand_value(hand)
                result = "draw"
                if player_score > 21 or (dealer_score <= 21 and dealer_score > player_score):
                    result = "lose"
                elif dealer_score > 21 or player_score > dealer_score:
                    result = "win"
                self.settle_hand(seat, index, result)
        self.round_complete = True
        self.awaiting_bet = True
        self.last_result = self._result_summary()
        logger.info(
            "Round complete. Dealer score {dealer_score}. Results: {results}",
            dealer_score=dealer_score,
            results=self.last_result,
        )

    def handle_surrender(self):
        """Resolve surrender on the current seat hand."""
        self.player.mark_current_hand("resolved", "surrender")
        self.settle_hand(self.player, self.player.active_hand_index, "surrender")
        round_finished = self._advance_or_resolve()
        if round_finished:
            self.last_result = self._result_summary()
