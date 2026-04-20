"""Routes for the blackjack game."""

from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    render_template,
    request,
    url_for,
)

from .models import Game
from ..tools.devtools_core import build_seeded_game, list_scenarios, parse_cards
from ..utils import load_game_state, save_game_state, setup_logging


logger = setup_logging("routes")
blackjack_bp = Blueprint("blackjack", __name__, template_folder="templates")


def _card_label(card):
    return f"{card.rank} of {card.suit}"


def _active_hand_payload(game):
    """Return display information for every hand on the active seat."""
    hands = []
    for index, hand in enumerate(game.player.hands):
        hands.append(
            {
                "label": f"Hand {index + 1}",
                "cards": ", ".join(_card_label(card) for card in hand)
                or "No cards dealt yet.",
                "value": game.player.hand_value_display(hand),
                "bet": game.player.hand_bets[index],
                "isActive": index == game.player.active_hand_index,
                "state": game.player.hand_states[index],
                "result": game.player.hand_results[index],
            }
        )
    return hands


def _dealer_display(game):
    if not game.dealer.hand:
        return "No cards dealt yet."
    if game.round_complete:
        return ", ".join(_card_label(card) for card in game.dealer.hand)
    visible_card = _card_label(game.dealer.hand[0])
    if len(game.dealer.hand) == 1:
        return visible_card
    return f"{visible_card}, Hidden"


def _seat_payloads(game):
    """Return all seven table spots, including empty placeholders."""
    seat_slots = [
        {
            "position": position,
            "occupied": False,
            "label": f"Seat {position + 1}",
            "cards": [],
            "hands": [],
            "bet": 0,
            "value": "",
            "isActive": False,
        }
        for position in range(7)
    ]
    for index, seat in enumerate(game.seats):
        compact_hands = []
        for hand_index, hand in enumerate(seat.hands):
            compact_hands.append(
                {
                    "cards": [card.serialize() for card in hand],
                    "value": seat.hand_value_display(hand),
                    "isActive": hand_index == seat.active_hand_index,
                    "state": seat.hand_states[hand_index],
                }
            )
        seat_slots[seat.table_position] = {
            "position": seat.table_position,
            "occupied": True,
            "label": seat.name,
            "cards": [card.serialize() for card in seat.hand],
            "hands": compact_hands,
            "bet": sum(seat.hand_bets),
            "value": seat.hand_value_display(),
            "isActive": index == game.active_seat_index and not game.awaiting_bet,
        }
    return seat_slots


def _strategy_advice_items(game):
    """Return structured round-result items for easier UI rendering."""
    if not (game.round_complete and game.last_result):
        return []
    return [item.strip() for item in game.last_result.split(", ") if item.strip()]


def _game_payload(game, message):
    """Build the JSON payload used by the front end."""
    active_hand = game.player.hand if game.seats else []
    dealer_value = game.dealer.hand_value_display() if game.round_complete else "Hidden"
    player_hand = (
        ", ".join(_card_label(card) for card in active_hand) or "No cards dealt yet."
    )
    strategy_advice = "Choose seats and place a bet to deal the next hand."
    if game.awaiting_bet and game.seat_count:
        strategy_advice = "Place a bet to deal the next hand."
    if (
        not game.awaiting_bet
        and active_hand
        and game.dealer.hand
        and game.player.current_state == "playing"
    ):
        strategy_advice = f"Suggested move: {game.determine_best_move(active_hand, game.dealer.hand[0])}"
    elif game.round_complete and game.last_result:
        strategy_advice = "Round complete."
    return {
        "message": message,
        "game": game.serialize(),
        "playerHand": player_hand,
        "dealerHand": _dealer_display(game),
        "playerValue": game.player.hand_value_display() if active_hand else 0,
        "dealerValue": dealer_value,
        "bankroll": game.bankroll,
        "currentBet": game.player.current_bet if game.seats else 0,
        "playerHands": _active_hand_payload(game),
        "activeHandIndex": game.player.active_hand_index,
        "activeSeatIndex": game.active_seat_index,
        "activeSeatLabel": game.player.name if game.seats else "",
        "canSplit": game.player.can_split(game.bankroll),
        "canDoubleDown": game.double_down(active_hand),
        "canSurrender": bool(game.dealer.hand)
        and game.surrender(active_hand, game.dealer.hand[0]),
        "awaitingBet": game.awaiting_bet,
        "roundComplete": game.round_complete,
        "lastResult": game.last_result,
        "strategyAdvice": strategy_advice,
        "strategyAdviceItems": _strategy_advice_items(game),
        "statusUrl": url_for("blackjack.game_status"),
        "seats": _seat_payloads(game),
        "seatCount": game.seat_count,
        "shoeRemaining": game.deck.remaining(),
        "shoeDecks": game.shoe_decks,
    }


def _devtools_enabled():
    return bool(current_app.config.get("DEVTOOLS_ENABLED"))


@blackjack_bp.route("/")
def index():
    logger.debug("Rendering blackjack index.")
    return render_template("index.html")


@blackjack_bp.route("/devtools/options")
def devtools_options():
    if not _devtools_enabled():
        return jsonify({"error": "Developer tools are disabled."}), 404
    return jsonify({"enabled": True, "scenarios": list_scenarios()})


@blackjack_bp.route("/devtools/seed", methods=["POST"])
def devtools_seed():
    if not _devtools_enabled():
        return jsonify({"error": "Developer tools are disabled."}), 404

    request_data = request.get_json(silent=True) or {}
    try:
        scenario_name = request_data.get("scenario")
        if scenario_name:
            scenario_map = {scenario["name"]: scenario for scenario in list_scenarios()}
            scenario = scenario_map.get(scenario_name)
            if scenario is None:
                raise ValueError(f"Unknown scenario '{scenario_name}'.")
            player_cards = [
                Game._deserialize_card(card_data) for card_data in scenario["player"]
            ]
            dealer_cards = [
                Game._deserialize_card(card_data) for card_data in scenario["dealer"]
            ]
            deck_cards = [
                Game._deserialize_card(card_data) for card_data in scenario["deck"]
            ]
            bet = int(request_data.get("bet", scenario["bet"]))
            bankroll = int(request_data.get("bankroll", scenario["bankroll"]))
        else:
            player_cards = parse_cards(request_data.get("player"))
            dealer_cards = parse_cards(request_data.get("dealer"))
            deck_cards = parse_cards(request_data.get("deck"))
            bet = int(request_data.get("bet", 100))
            bankroll = int(request_data.get("bankroll", 1000))

        if not player_cards or not dealer_cards:
            raise ValueError(
                "Provide both player and dealer cards to seed a test hand."
            )

        game = build_seeded_game(
            player_cards=player_cards,
            dealer_cards=dealer_cards,
            deck_cards=deck_cards,
            bet=bet,
            bankroll=bankroll,
            active_hand_index=int(request_data.get("activeHandIndex", 0)),
            awaiting_bet=bool(request_data.get("awaitingBet", False)),
            round_complete=bool(request_data.get("roundComplete", False)),
            last_result=request_data.get("lastResult", ""),
        )
        save_game_state(game)
        return jsonify(_game_payload(game, "Devtools scenario applied."))
    except ValueError as error:
        logger.warning("Devtools seed rejected: {error}", error=str(error))
        return jsonify({"error": str(error)}), 400


@blackjack_bp.route("/start", methods=["POST"])
def start_game():
    """Start or reset the table and configure seat count if requested."""
    request_data = request.get_json(silent=True) or {}
    seat_count = request_data.get("seatCount")
    if seat_count is None:
        seat_count = request.form.get("seatCount", type=int)

    game = load_game_state()
    if game is None:
        game = Game(seat_count=seat_count or 1)
    else:
        game.reset_for_new_game(seat_count=seat_count or game.seat_count)
    save_game_state(game)
    return jsonify(
        _game_payload(game, "Table ready. Place a bet to deal the next hand.")
    )


@blackjack_bp.route("/bet", methods=["POST"])
def place_bet():
    """Place the same opening bet on every occupied seat."""
    game = load_game_state()
    if not game:
        return jsonify({"error": "Start a new game before betting."}), 400

    request_data = request.get_json(silent=True) or {}
    bet = request_data.get("bet")
    if bet is None:
        bet = request.form.get("bet", type=int)
    else:
        bet = int(bet)

    try:
        if not game.awaiting_bet and any(seat.hands[0] for seat in game.seats):
            return (
                jsonify(
                    {"error": "Finish the current hand before placing another bet."}
                ),
                400,
            )
        game.place_bets(bet)
        game.start_new_round()
        save_game_state(game)
        return jsonify(
            _game_payload(
                game, f"Bet placed: {bet} on {game.seat_count} seats. New hand dealt."
            )
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@blackjack_bp.route("/game_status")
def game_status():
    game = load_game_state()
    if not game:
        flash("No active game found. Please start a new game.")
        return render_template("index.html")
    return render_template("status.html", game=game)


@blackjack_bp.route("/action/<action>", methods=["POST"])
def handle_action(action):
    """Handle player actions on the current active seat."""
    game = load_game_state()
    if not game:
        return jsonify({"error": "No game in progress"}), 400

    if game.awaiting_bet and not any(seat.hands[0] for seat in game.seats):
        return jsonify({"error": "Place a bet before taking an action."}), 400

    try:
        current_seat = game.player
        if current_seat.current_state != "playing":
            return jsonify({"error": "This hand is no longer active."}), 400

        if action == "hit":
            current_seat.add_card(game.deck.deal())
            if current_seat.hand_value() > 21:
                current_seat.mark_current_hand("resolved", "lose")
                game.settle_hand(current_seat, current_seat.active_hand_index, "lose")
                finished = game._advance_or_resolve()
                save_game_state(game)
                if finished:
                    return jsonify(_game_payload(game, "Hand busted. Round resolved."))
                return jsonify(
                    _game_payload(
                        game,
                        f"Hand busted. Moved to {game.player.name} Hand {game.player.active_hand_index + 1}.",
                    )
                )
            save_game_state(game)
            return jsonify(
                _game_payload(game, f"Performed hit on {current_seat.name}.")
            )

        if action == "stand":
            current_seat.mark_current_hand("stood")
            finished = game._advance_or_resolve()
            save_game_state(game)
            if finished:
                return jsonify(_game_payload(game, "Round resolved."))
            return jsonify(
                _game_payload(
                    game,
                    f"Moved to {game.player.name} Hand {game.player.active_hand_index + 1}.",
                )
            )

        if action == "double_down":
            if not game.double_down(current_seat.hand):
                return jsonify({"error": "Double down not allowed"}), 400
            current_index = current_seat.active_hand_index
            current_seat.hand_bets[current_index] *= 2
            current_seat.add_card(game.deck.deal())
            if current_seat.hand_value() > 21:
                current_seat.set_hand_state(current_index, "resolved", "lose")
                game.settle_hand(current_seat, current_index, "lose")
            else:
                current_seat.set_hand_state(current_index, "stood")
            finished = game._advance_or_resolve()
            save_game_state(game)
            if finished:
                return jsonify(
                    _game_payload(game, "Performed double down and resolved the round.")
                )
            return jsonify(
                _game_payload(
                    game,
                    f"Performed double down. Moved to {game.player.name} Hand {game.player.active_hand_index + 1}.",
                )
            )

        if action == "split":
            if not current_seat.can_split(game.bankroll):
                return jsonify({"error": "Cannot split this hand"}), 400
            current_seat.split(game.deck)
            save_game_state(game)
            return jsonify(
                _game_payload(game, f"Split {current_seat.name} into two hands.")
            )

        if action == "surrender":
            game.handle_surrender()
            save_game_state(game)
            return jsonify(_game_payload(game, game.last_result or "Surrender"))

        return jsonify({"error": "Invalid action"}), 400
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@blackjack_bp.route("/double_down", methods=["POST"])
def double_down():
    return handle_action("double_down")


@blackjack_bp.route("/split", methods=["POST"])
def split():
    return handle_action("split")
