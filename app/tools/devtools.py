"""Developer tools for exercising the blackjack app in a controlled way.

This module provides a small harness around Flask's ``test_client`` so we can:

- boot the application without running a browser,
- seed deterministic game states directly into the session,
- replay action sequences quickly against the real routes,
- capture consistent JSON snapshots while Loguru records the flow.

Example usage:

```powershell
python -m app.tools.devtools --scenario split_eights --action hit --action stand --log-level DEBUG
python -m app.tools.devtools --player "A-Hearts,6-Clubs" --dealer "5-Spades,K-Diamonds" --bet 50 --show-status
```
"""

from __future__ import annotations

import argparse
import json
import os

from app import create_app
from app.blackjack.models import Game
from app.utils import setup_logging
from .devtools_core import (
    SCENARIOS,
    build_seeded_game,
    cards_to_text,
    parse_card,
    parse_cards,
)


logger = setup_logging("devtools")


class BlackjackDevTools:
    """Controlled harness for route-level gameplay testing."""

    def __init__(self, log_level: str = "INFO"):
        os.environ["FLASK_CONFIG"] = "TestingConfig"
        os.environ["BLACKJACK_LOG_LEVEL"] = log_level.upper()
        self.logger = setup_logging("devtools", log_level.upper())
        self.app = create_app("TestingConfig")
        self.app.config.update(TESTING=True, SECRET_KEY="devtools-secret")
        self.client = self.app.test_client()

    def start(self) -> dict:
        """Reset the game session using the real start endpoint."""
        self.logger.info("Starting a fresh devtools session.")
        response = self.client.post("/blackjack/start")
        return self._json_response(response, "start")

    def place_bet(self, bet: int) -> dict:
        """Place a bet using the real route."""
        self.logger.info("Placing devtools bet of {bet}.", bet=bet)
        response = self.client.post("/blackjack/bet", json={"bet": bet})
        return self._json_response(response, "bet")

    def action(self, action_name: str) -> dict:
        """Perform a blackjack action against the route layer."""
        self.logger.info("Executing action {action}.", action=action_name)
        response = self.client.post(f"/blackjack/action/{action_name}")
        return self._json_response(response, action_name)

    def status_page(self) -> dict:
        """Fetch the status page and report simple diagnostics."""
        response = self.client.get("/blackjack/game_status")
        html = response.get_data(as_text=True)
        self.logger.info("Fetched status page with HTTP {status}.", status=response.status_code)
        return {
            "status_code": response.status_code,
            "contains_strategy": "Strategy Guide" in html,
            "contains_table_status": "Table Status" in html,
            "contains_player_hands": "Player Hands" in html,
            "html_length": len(html),
        }

    def seed_round(
        self,
        *,
        player_cards: list[Card],
        dealer_cards: list[Card],
        deck_cards: list[Card] | None = None,
        bet: int = 100,
        bankroll: int = 1000,
        active_hand_index: int = 0,
        awaiting_bet: bool = False,
        round_complete: bool = False,
        last_result: str = "",
    ) -> dict:
        """Inject a deterministic round state into the session."""
        game = build_seeded_game(
            player_cards=player_cards,
            dealer_cards=dealer_cards,
            deck_cards=deck_cards,
            bet=bet,
            bankroll=bankroll,
            active_hand_index=active_hand_index,
            awaiting_bet=awaiting_bet,
            round_complete=round_complete,
            last_result=last_result,
        )

        with self.client.session_transaction() as session:
            session["game_state"] = game.serialize()

        self.logger.info(
            "Seeded round: player={player} dealer={dealer} deck_depth={deck_depth} bet={bet} bankroll={bankroll}",
            player=cards_to_text(player_cards),
            dealer=cards_to_text(dealer_cards),
            deck_depth=len(deck_cards or []),
            bet=bet,
            bankroll=bankroll,
        )
        return self.snapshot()

    def apply_scenario(self, name: str) -> dict:
        """Load one of the built-in deterministic scenarios."""
        scenario = SCENARIOS[name]
        self.logger.info("Applying scenario {name}: {description}", name=name, description=scenario.description)
        return self.seed_round(
            player_cards=[parse_card(card) for card in scenario.player],
            dealer_cards=[parse_card(card) for card in scenario.dealer],
            deck_cards=[parse_card(card) for card in scenario.deck],
            bet=scenario.bet,
            bankroll=scenario.bankroll,
        )

    def snapshot(self) -> dict:
        """Return the current serialized game state."""
        with self.client.session_transaction() as session:
            state = session.get("game_state")

        if not state:
            self.logger.warning("Snapshot requested with no game state in session.")
            return {}

        game = Game.from_dict(state)
        snapshot = {
            "bankroll": game.player.bankroll,
            "current_bet": game.player.current_bet,
            "awaiting_bet": game.awaiting_bet,
            "round_complete": game.round_complete,
            "last_result": game.last_result,
            "active_hand_index": game.player.active_hand_index,
            "player_hands": [cards_to_text(hand) for hand in game.player.hands],
            "dealer_hand": cards_to_text(game.dealer.hand),
            "deck_depth": len(game.deck.cards),
        }
        self.logger.debug("Current snapshot: {snapshot}", snapshot=snapshot)
        return snapshot

    def run_sequence(self, actions: list[str]) -> list[dict]:
        """Run a sequence of actions and collect route payloads."""
        results = []
        for action_name in actions:
            results.append({"action": action_name, "result": self.action(action_name)})
        return results

    def _json_response(self, response, label: str) -> dict:
        """Normalize JSON responses and log failures clearly."""
        payload = response.get_json(silent=True)
        if response.status_code >= 400:
            self.logger.error(
                "Route {label} failed with HTTP {status}: {payload}",
                label=label,
                status=response.status_code,
                payload=payload,
            )
        else:
            self.logger.debug(
                "Route {label} returned HTTP {status}: {payload}",
                label=label,
                status=response.status_code,
                payload=payload,
            )
        return {
            "status_code": response.status_code,
            "payload": payload,
        }


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for the devtools harness."""
    parser = argparse.ArgumentParser(
        description="Exercise the blackjack app deterministically through Flask devtools."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Loguru level to use for the devtools harness.",
    )
    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIOS.keys()),
        help="Apply a built-in deterministic round setup.",
    )
    parser.add_argument(
        "--player",
        help="Comma-delimited player cards, e.g. '8-Clubs,8-Diamonds'.",
    )
    parser.add_argument(
        "--dealer",
        help="Comma-delimited dealer cards, e.g. '6-Hearts,Q-Spades'.",
    )
    parser.add_argument(
        "--deck",
        help="Comma-delimited top-of-deck cards for subsequent actions.",
    )
    parser.add_argument(
        "--bet",
        type=int,
        default=100,
        help="Bet used for seeded rounds or the live bet route.",
    )
    parser.add_argument(
        "--bankroll",
        type=int,
        default=1000,
        help="Bankroll used for seeded rounds.",
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Call /blackjack/start before any other command.",
    )
    parser.add_argument(
        "--place-bet",
        action="store_true",
        help="Call /blackjack/bet with --bet after starting the session.",
    )
    parser.add_argument(
        "--action",
        action="append",
        default=[],
        help="Action to perform after setup. Repeat for sequences.",
    )
    parser.add_argument(
        "--show-status",
        action="store_true",
        help="Fetch the rendered status page and include a small diagnostic summary.",
    )
    return parser


def main() -> int:
    """Run the CLI harness and print a compact JSON report."""
    parser = build_parser()
    args = parser.parse_args()
    tools = BlackjackDevTools(log_level=args.log_level)

    report = {"steps": []}

    if args.start:
        report["steps"].append({"start": tools.start()})

    if args.scenario:
        report["steps"].append({"scenario": args.scenario, "snapshot": tools.apply_scenario(args.scenario)})
    elif args.player and args.dealer:
        report["steps"].append(
            {
                "seeded_round": tools.seed_round(
                    player_cards=parse_cards(args.player),
                    dealer_cards=parse_cards(args.dealer),
                    deck_cards=parse_cards(args.deck),
                    bet=args.bet,
                    bankroll=args.bankroll,
                )
            }
        )

    if args.place_bet:
        report["steps"].append({"bet": tools.place_bet(args.bet)})

    if args.action:
        report["steps"].append({"actions": tools.run_sequence(args.action)})

    if args.show_status:
        report["steps"].append({"status_page": tools.status_page()})

    report["final_snapshot"] = tools.snapshot()
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
