# app/utils/helpers

import logging
from flask import session


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

def calculate_hand_value(hand):
    """Calculate the total value of a hand, adjust for aces as needed."""
    total = sum(assign_value(card) for card in hand)
    aces = sum(1 for card in hand if card.rank == 'A')
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def assign_value(rank):
    """Calculate the value of a card, special handling for aces."""
    if rank in ["J", "Q", "K"]:
        return 10
    elif rank == "A":
        return 11
    return int(rank)
