import os
import sys
from datetime import datetime
from pathlib import Path
from flask import session
from loguru import logger


_LOGGING_CONFIGURED = False
_LOG_FILE_SIZE_LIMIT = 10 * 1024 * 1024


def _project_log_path():
    """Return the default timestamped log file path under the repo logs folder."""
    logs_dir = Path(__file__).resolve().parents[2] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir / "blackjack-{time:YYYYMMDDHHmmss}.log"


def _prepare_sink_path(raw_sink):
    """Normalize a configured file sink and ensure its parent directory exists."""
    sink_path = Path(raw_sink)
    sink_path.parent.mkdir(parents=True, exist_ok=True)
    return str(sink_path)


def _rotate_daily_or_size(message, file_object):
    """Rotate when the day changes or the current log exceeds 10 MB."""
    record_time = message.record["time"]
    file_path = Path(file_object.name)
    try:
        if not file_path.exists():
            return False
        file_stats = file_path.stat()
        if file_stats.st_size >= _LOG_FILE_SIZE_LIMIT:
            return True
    except OSError:
        return False
    file_date = datetime.fromtimestamp(file_stats.st_mtime).date()
    return record_time.date() != file_date


def setup_logging(name=None, level=None):
    """Set up the application's logging configuration with loguru."""
    global _LOGGING_CONFIGURED  # pylint: disable=global-statement

    log_level = level or os.getenv("BLACKJACK_LOG_LEVEL", "WARNING").upper()
    if not _LOGGING_CONFIGURED:
        configured_sink = os.getenv("BLACKJACK_LOG_SINK")
        sink = _prepare_sink_path(configured_sink) if configured_sink else str(_project_log_path())
        keep_console = os.getenv("BLACKJACK_LOG_TO_CONSOLE", "1") == "1"
        retention = int(os.getenv("BLACKJACK_LOG_RETENTION", "14"))
        sink_supports_rotation = "{time" in sink
        logger.remove()
        file_sink_options = dict(
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[name]} | {message}",
        )
        if sink_supports_rotation:
            file_sink_options["rotation"] = _rotate_daily_or_size
            file_sink_options["retention"] = retention
        logger.add(
            sink,
            **file_sink_options,
        )
        if keep_console:
            logger.add(
                sys.stderr,
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

def format_hand_value(hand):
    """Return a display-friendly hand total, including soft totals when useful."""
    total = calculate_hand_value(hand)
    aces = sum(1 for card in hand if card.rank == "A")
    if not aces:
        return str(total)

    hard_total = sum(1 if card.rank == "A" else assign_value(card.rank) for card in hand)
    soft_total = hard_total + 10
    if soft_total <= 21 and soft_total != hard_total:
        return f"{hard_total} / {soft_total}"
    return str(total)

def assign_value(rank):
    """Calculate the value of a card, special handling for aces."""
    if rank in ["J", "Q", "K"]:
        return 10
    elif rank == "A":
        return 11
    return int(rank)
