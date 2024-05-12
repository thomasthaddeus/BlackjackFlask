# app/utils/helpers

import csv
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

def setup_logging():
    """Set up the application's logging configuration."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger('BlackjackGame')

def save_game_state(game_state):
    """Save current game state to session."""
    session["game_state"] = game_state

def load_game_state():
    """Load game state from session."""
    return session.get("game_state", None)