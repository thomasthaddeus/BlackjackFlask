"""blackjack/routes.py

This module defines the routes for the blackjack game.

Returns:
    Various types based on the routes, primarily dealing with game state and player actions.
"""

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    jsonify,
)
from .models import Game
from ..utils import save_game_state, load_game_state, setup_logging

logger = setup_logging()
blackjack_bp = Blueprint("blackjack", __name__, template_folder="templates")

@blackjack_bp.route("/")
def index():
    """Render the index page."""
    return render_template("index.html")

@blackjack_bp.route("/start", methods=["POST"])
def start_game():
    """Start a new game and save it to the session."""
    game = Game()  # Create a new game instance
    game.start_new_round()  # Start a new round
    save_game_state(game)  # Save game instance to session
    return redirect(url_for("blackjack.game_status"))

@blackjack_bp.route("/bet", methods=["POST"])
def place_bet():
    """Place a bet for the current game."""
    game = load_game_state()
    if not game:
        flash("Start a new game before betting.")
        return redirect(url_for("blackjack.index"))

    bet = request.form.get("bet", type=int)
    try:
        game.player.place_bet(bet)
        save_game_state(game)
        return redirect(url_for("blackjack.game_status"))
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("blackjack.index"))

@blackjack_bp.route("/game_status")
def game_status():
    """Render the game status page."""
    game = load_game_state()
    if not game:
        flash("No active game found. Please start a new game.")
        return redirect(url_for("blackjack.index"))
    return render_template("status.html", game=game)

@blackjack_bp.route("/action/<action>", methods=["POST"])
def handle_action(action):
    """Handle player actions like hit, stand, double down, split, and surrender."""
    game = load_game_state()
    if not game:
        return jsonify({"error": "No game in progress"}), 400

    try:
        if action == "hit":
            game.player.add_card(game.deck.deal())
        elif action == "stand":
            # Stand logic can be handled in the game class, e.g., game.player.stand()
            pass
        elif action == "double_down":
            if game.double_down(game.player.hand):
                game.player.add_card(game.deck.deal())
        elif action == "split":
            if game.player.can_split():
                game.player.split()
        elif action == "surrender":
            game.handle_surrender()
        else:
            return jsonify({"error": "Invalid action"}), 400

        save_game_state(game)  # Save changes to session
        return jsonify(
            {"message": f"Performed {action}", "game": game.serialize()}
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@blackjack_bp.route("/double_down", methods=["POST"])
def double_down():
    """Handle double down action."""
    game = load_game_state()
    if not game or not game.double_down(game.player.hand):
        flash("Double down not allowed at this stage.")
        return redirect(url_for("blackjack.game_status"))

    game.player.place_bet(game.player.current_bet)  # Double the bet
    game.player.add_card(game.deck.deal())
    save_game_state(game)
    return redirect(url_for("blackjack.game_status"))

@blackjack_bp.route("/split", methods=["POST"])
def split():
    """Handle split action."""
    game = load_game_state()
    if not game or not game.player.can_split():
        flash("Cannot split at this time.")
        return redirect(url_for("blackjack.game_status"))

    game.player.split()
    save_game_state(game)
    return redirect(url_for("blackjack.game_status"))
