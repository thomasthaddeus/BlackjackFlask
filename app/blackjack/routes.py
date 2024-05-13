"""blackjack/routes.py
_summary_

_extended_summary_

Returns:
    _type_: _description_
"""

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    session,
    flash,
    jsonify,
)
from .models import Game
from ..utils import save_game_state, load_game_state, setup_logging

logger = setup_logging()
blackjack_bp = Blueprint("blackjack", __name__, template_folder="templates")


@blackjack_bp.route("/")
def index():
    return render_template("index.html")

@blackjack_bp.route("/start", methods=["POST"])
def start_game():
    game = Game()  # Create a new game instance
    game.start_new_round()  # Start a new round
    session["game"] = game  # Save game instance to session
    return redirect(url_for("blackjack.game_status"))

@blackjack_bp.route("/bet", methods=["POST"])
def place_bet():
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
    game = load_game_state()
    if not game:
        flash("No active game found. Please start a new game.")
        return redirect(url_for("blackjack.index"))
    # Assuming the game can tell us the current state and suggestions
    return render_template("status.html", game=game)

@blackjack_bp.route("/action/<action>", methods=["POST"])
def handle_action(action):
    game = load_game_state()
    if not game:
        return jsonify({"error": "No game in progress"}), 400

    if action in ["hit", "stand", "double_down", "split", "surrender"]:
        getattr(game.player, action)(game.deck)  # Assume these methods exist
        save_game_state(game)  # Save changes to session
        return jsonify(
            {"message": f"Performed {action}", "game": game.serialize()}
        )  # Ensure game can serialize its state

    return jsonify({"error": "Invalid action"}), 400

@blackjack_bp.route("/double_down", methods=["POST"])
def double_down():
    game = load_game_state()
    if not game or not game.double_down(game.player.hand):
        flash("Double down not allowed at this stage.")
        return redirect(url_for("blackjack.game_status"))

    game.player.double_down(game.deck)
    return redirect(url_for("blackjack.game_status"))

@blackjack_bp.route("/split", methods=["POST"])
def split():
    game = load_game_state()
    if not game or not game.player.can_split():
        flash("Cannot split at this time.")
        return redirect(url_for("blackjack.game_status"))

    game.player.split()
    return redirect(url_for("blackjack.game_status"))
