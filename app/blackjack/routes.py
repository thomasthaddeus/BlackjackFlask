# blackjack/routes.py

import logging
from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from .models import Game
from ..utils import (
    save_game_state,
    load_game_state,
    setup_logging,
)

setup_logging()

# Define the blueprint
blackjack_bp = Blueprint("blackjack", __name__)


@blackjack_bp.route("/")
def index():
    return render_template("index.html")

@blackjack_bp.route("/start", methods=["POST"])
def start_game():
    session["game"] = Game()  # Create a new game instance
    session["game"].start_new_round()  # Start a new round
    save_game_state(session["game"])  # Save game state to session
    return redirect(url_for("blackjack.game_status"))

@blackjack_bp.route("/bet", methods=["POST"])
def place_bet():
    bet = request.form.get("bet", type=int)
    try:
        if bet is None or bet < 0:
            logging.warning("Attempt to place invalid bet amount")
            flash("Invalid bet amount. Please enter a valid number.")
            return redirect(url_for("blackjack.index"))
        session["bet"] = bet
        logging.info("Bet placed: %s", bet)
        save_game_state(session)  # Update session after placing bet
        return redirect(url_for("blackjack.game_status"))
    except Exception as e:
        logging.error("Error placing bet: %s", str(e))
        flash("An error occurred while placing the bet.")
        return redirect(url_for("blackjack.index"))

@blackjack_bp.route("/game_status")
def game_status():
    game = load_game_state()  # Load the game state from the session
    if not game:
        flash("No active game found. Please start a new game.")
        return redirect(url_for("blackjack.index"))

    player_hand = game.player.hand
    dealer_hand = game.dealer.hand if game.dealer_turn_over else []

    # Determine best move suggestion
    if not game.dealer_turn_over:
        best_move = game.determine_best_move(
            player_hand, dealer_hand[0]
        )  # Assuming dealer's visible card is the first card
        flash(f"Suggested move: {best_move}")

    return render_template("status.html", game=game)


@blackjack_bp.route("/hit", methods=["POST"])
def hit():
    game = load_game_state()
    if not game:
        flash("No game in progress. Please start a new game.")
        return redirect(url_for("blackjack.index"))

    game.player.hit(game.deck)
    save_game_state(game)
    return redirect(url_for("blackjack.game_status"))


@blackjack_bp.route("/double_down", methods=["POST"])
def double_down():
    game = load_game_state()
    if not game or not game.double_down(game.player.hand):
        flash("Double down not allowed at this stage.")
        return redirect(url_for("blackjack.game_status"))

    game.player.double_down(game.deck)
    save_game_state(game)
    return redirect(url_for("blackjack.game_status"))


@blackjack_bp.route("/split", methods=["POST"])
def split():
    game = load_game_state()
    if not game or not game.player.can_split():
        flash("Cannot split at this time.")
        return redirect(url_for("blackjack.game_status"))

    game.player.split()
    save_game_state(game)
    return redirect(url_for("blackjack.game_status"))
