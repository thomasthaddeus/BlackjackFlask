# app/utils/helpers

import os
import sys
from flask import session
from loguru import logger


_LOGGING_CONFIGURED = False


def setup_logging(name=None, level=None):
    """Set up the application's logging configuration with loguru."""
    global _LOGGING_CONFIGURED  # pylint: disable=global-statement

    log_level = level or os.getenv("BLACKJACK_LOG_LEVEL", "WARNING").upper()
    if not _LOGGING_CONFIGURED:
        sink = os.getenv("BLACKJACK_LOG_SINK")
        logger.remove()
        logger.add(
            sink or sys.stderr,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[name]} | {message}",
        )
        _LOGGING_CONFIGURED = True

    return logger.bind(name=name or "BlackjackGame")

def save_game_state(game_state):
    """Save current game state to session."""
    session["game_state"] = game_state.serialize()
    setup_logging("session").debug("Saved game state to session.")

def load_game_state():
    """Load game state from session."""
    game_state = session.get("game_state")
    if game_state is None:
        setup_logging("session").debug("No game state found in session.")
        return None

    from ..blackjack.models import Game  # pylint: disable=import-outside-toplevel

    setup_logging("session").debug("Loaded game state from session.")
    return Game.from_dict(game_state)

def calculate_hand_value(hand):
    """Calculate the total value of a hand, adjust for aces as needed."""
    total = sum(assign_value(card.rank) for card in hand)
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
