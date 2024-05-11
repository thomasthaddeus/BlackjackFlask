# app/utils/helpers

import csv
from random import shuffle
import logging
from flask import session

def get_card_value(card):
    """Calculate the value of a card, special handling for aces."""
    if card.rank in ['J', 'Q', 'K']:
        return 10
    elif card.rank == 'A':
        return 11  # Initial value of ace
    return int(card.rank)

def calculate_hand_value(hand):
    """Calculate the total value of a hand, adjust for aces as needed."""
    total = sum(get_card_value(card) for card in hand)
    aces = sum(1 for card in hand if card.rank == 'A')
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def load_strategy(filename):
    """
    Load blackjack strategy from a CSV file into a dictionary.

    :param filename: Path to the CSV file containing the strategy.
    :return: Dictionary with player hands as keys and sub-dictionaries as values,
             where each sub-dictionary maps dealer's card to an action.
    """
    strategy = {}
    with open(filename, mode="r", encoding='utf-8', newline="") as file:
        reader = csv.reader(file)
        headers = next(reader)[1:]  # Skip the first header for 'my_hand'

        for row in reader:
            hand = row[0]  # Player's hand (e.g., '8', '9', 'a2', 'd2')
            actions = row[1:]
            strategy[hand] = dict(zip(headers, actions))

    return strategy

def determine_best_move(player_hand, dealer_card):
    """Determine the best move ('hit' or 'stand') based on blackjack strategy."""
    player_value = calculate_hand_value(player_hand)
    dealer_value = get_card_value(dealer_card)
    # This could be enhanced with a more complex strategy logic
    if player_value < 17:
        return 'hit'
    return 'stand'

def shuffle_deck(deck):
    """Shuffle the deck of cards."""
    shuffle(deck)
    return deck

def setup_logging():
    """Set up the application's logging configuration."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger('BlackjackGame')

def save_game_state(game_state):
    """Save current game state to session."""
    session['game_state'] = game_state

def load_game_state():
    """Load game state from session."""
    return session.get('game_state', None)
