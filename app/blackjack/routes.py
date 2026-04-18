"""blackjack/routes.py

This module defines the routes for the blackjack game.

Returns:
    Various types based on the routes, primarily dealing with game state and player actions.
"""

from flask import (
    Blueprint,
    render_template,
    url_for,
    request,
    flash,
    jsonify,
)
from .models import Game
from ..utils import save_game_state, load_game_state, setup_logging

logger = setup_logging()
blackjack_bp = Blueprint("blackjack", __name__, template_folder="templates")


def _card_label(card):
    """Format a card for display."""
    return f"{card.rank} of {card.suit}"


def _hand_payload(game):
    """Return display information for every player hand."""
    hands = []
    for index, hand in enumerate(game.player.hands):
        hands.append(
            {
                "label": f"Hand {index + 1}",
                "cards": ", ".join(_card_label(card) for card in hand) or "No cards dealt yet.",
                "value": game.player.hand_value(hand),
                "bet": game.player.hand_bets[index],
                "isActive": index == game.player.active_hand_index,
            }
        )
    return hands


def _dealer_display(game):
    """Return the dealer hand string for the current game state."""
    if not game.dealer.hand:
        return "No cards dealt yet."
    if game.round_complete:
        return ", ".join(_card_label(card) for card in game.dealer.hand)
    visible_card = _card_label(game.dealer.hand[0])
    if len(game.dealer.hand) == 1:
        return visible_card
    return f"{visible_card}, Hidden"


def _game_payload(game, message):
    """Build the JSON payload used by the front end."""
    active_hand = game.player.hand
    dealer_value = game.dealer.hand_value() if game.round_complete else "Hidden"
    player_hand = ", ".join(_card_label(card) for card in active_hand) or "No cards dealt yet."
    return {
        "message": message,
        "game": game.serialize(),
        "playerHand": player_hand,
        "dealerHand": _dealer_display(game),
        "playerValue": game.player.hand_value() if active_hand else 0,
        "dealerValue": dealer_value,
        "bankroll": game.player.bankroll,
        "currentBet": game.player.current_bet,
        "playerHands": _hand_payload(game),
        "activeHandIndex": game.player.active_hand_index,
        "canSplit": game.player.can_split(),
        "awaitingBet": game.awaiting_bet,
        "roundComplete": game.round_complete,
        "lastResult": game.last_result,
        "statusUrl": url_for("blackjack.game_status"),
    }

@blackjack_bp.route("/")
def index():
    """Render the index page."""
    logger.debug("Rendering blackjack index.")
    return render_template("index.html")

@blackjack_bp.route("/start", methods=["POST"])
def start_game():
    """Start a new game and save it to the session."""
    game = load_game_state()
    if game is None:
        logger.info("Starting first game for session.")
        game = Game()
    else:
        logger.info("Starting new game while preserving bankroll.")
        game.reset_for_new_game()
    save_game_state(game)
    return jsonify(_game_payload(game, "New game ready. Place a bet to deal the next hand."))

@blackjack_bp.route("/bet", methods=["POST"])
def place_bet():
    """Place a bet for the current game."""
    game = load_game_state()
    if not game:
        logger.warning("Bet attempted without an active game.")
        return jsonify({"error": "Start a new game before betting."}), 400

    request_data = request.get_json(silent=True) or {}
    bet = request_data.get("bet")
    if bet is None:
        bet = request.form.get("bet", type=int)
    else:
        bet = int(bet)
    try:
        if not game.awaiting_bet and game.player.hand:
            logger.warning("Bet attempted while round is still active.")
            return jsonify({"error": "Finish the current hand before placing another bet."}), 400
        game.player.place_bet(bet)
        game.start_new_round()
        game.player.current_bet = bet
        save_game_state(game)
        logger.info("Accepted bet {bet} and dealt a new hand.", bet=bet)
        return jsonify(_game_payload(game, f"Bet placed: {bet}. New hand dealt."))
    except ValueError as e:
        logger.warning("Rejected bet: {error}", error=str(e))
        return jsonify({"error": str(e)}), 400

@blackjack_bp.route("/game_status")
def game_status():
    """Render the game status page."""
    game = load_game_state()
    if not game:
        flash("No active game found. Please start a new game.")
        logger.info("Game status requested without active game.")
        return render_template("index.html")
    logger.debug("Rendering game status page.")
    return render_template("status.html", game=game)

@blackjack_bp.route("/action/<action>", methods=["POST"])
def handle_action(action):
    """Handle player actions like hit, stand, double down, split, and surrender."""
    game = load_game_state()
    if not game:
        logger.warning("Action {action} attempted without active game.", action=action)
        return jsonify({"error": "No game in progress"}), 400

    try:
        if game.awaiting_bet and not game.player.hand:
            logger.warning("Action {action} attempted before placing a bet.", action=action)
            return jsonify({"error": "Place a bet before taking an action."}), 400
        logger.info("Handling action {action} on hand {hand_index}.", action=action, hand_index=game.player.active_hand_index + 1)
        if action == "hit":
            game.player.add_card(game.deck.deal())
            if game.player.hand_value() > 21:
                round_finished = game._advance_or_resolve()
                if round_finished:
                    save_game_state(game)
                    return jsonify(_game_payload(game, "Hand busted. Round resolved."))
                save_game_state(game)
                return jsonify(
                    _game_payload(
                        game,
                        f"Hand busted. Moved to hand {game.player.active_hand_index + 1}.",
                    )
                )
        elif action == "stand":
            round_finished = game._advance_or_resolve()
            if round_finished:
                save_game_state(game)
                return jsonify(_game_payload(game, "Round resolved."))
            save_game_state(game)
            return jsonify(
                _game_payload(
                    game,
                    f"Moved to hand {game.player.active_hand_index + 1}.",
                )
            )
        elif action == "double_down":
            if game.double_down(game.player.hand):
                game.player.add_card(game.deck.deal())
                round_finished = game._advance_or_resolve()
                if round_finished:
                    save_game_state(game)
                    return jsonify(_game_payload(game, "Performed double_down and resolved the round."))
                save_game_state(game)
                return jsonify(
                    _game_payload(
                        game,
                        f"Performed double_down. Moved to hand {game.player.active_hand_index + 1}.",
                    )
                )
            else:
                return jsonify({"error": "Double down not allowed"}), 400
        elif action == "split":
            game.player.split(game.deck)
        elif action == "surrender":
            game.handle_surrender()
        else:
            logger.warning("Invalid action requested: {action}", action=action)
            return jsonify({"error": "Invalid action"}), 400

        save_game_state(game)  # Save changes to session
        message = game.last_result if game.round_complete and game.last_result else f"Performed {action}"
        return jsonify(_game_payload(game, message))
    except ValueError as e:
        logger.warning("Action {action} failed: {error}", action=action, error=str(e))
        return jsonify({"error": str(e)}), 400

@blackjack_bp.route("/double_down", methods=["POST"])
def double_down():
    """Handle double down action."""
    game = load_game_state()
    if not game or not game.double_down(game.player.hand):
        logger.warning("Double down requested when not allowed.")
        return jsonify({"error": "Double down not allowed at this stage."}), 400

    game.player.place_bet(game.player.current_bet)  # Double the bet
    game.player.add_card(game.deck.deal())
    save_game_state(game)
    logger.info("Double down route completed successfully.")
    return jsonify(_game_payload(game, "Performed double_down"))

@blackjack_bp.route("/split", methods=["POST"])
def split():
    """Handle split action."""
    game = load_game_state()
    if not game:
        logger.warning("Split requested without an active game.")
        return jsonify({"error": "No game in progress"}), 400

    try:
        game.player.split(game.deck)
    except ValueError as e:
        logger.warning("Split rejected: {error}", error=str(e))
        return jsonify({"error": str(e)}), 400

    save_game_state(game)
    logger.info("Split route completed successfully.")
    return jsonify(_game_payload(game, "Performed split"))
