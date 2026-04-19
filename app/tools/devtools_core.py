"""Shared helpers for developer-facing blackjack tooling."""

from __future__ import annotations

from dataclasses import dataclass

from app.blackjack.models import Card, Game


SUIT_ALIASES = {
    "h": "Hearts",
    "heart": "Hearts",
    "hearts": "Hearts",
    "d": "Diamonds",
    "diamond": "Diamonds",
    "diamonds": "Diamonds",
    "c": "Clubs",
    "club": "Clubs",
    "clubs": "Clubs",
    "s": "Spades",
    "spade": "Spades",
    "spades": "Spades",
}


@dataclass(frozen=True)
class Scenario:
    """Named deterministic setup for a specific gameplay situation."""

    player: list[str]
    dealer: list[str]
    deck: list[str]
    bet: int = 100
    bankroll: int = 1000
    description: str = ""


SCENARIOS = {
    "soft_ace": Scenario(
        player=["A-Hearts", "6-Clubs"],
        dealer=["5-Spades", "K-Diamonds"],
        deck=["4-Hearts", "9-Clubs", "2-Spades"],
        description="Soft-total strategy and follow-up hit validation.",
    ),
    "hard_nineteen": Scenario(
        player=["8-Clubs", "4-Hearts", "7-Hearts"],
        dealer=["2-Hearts", "Q-Spades"],
        deck=["5-Clubs", "10-Diamonds"],
        description="Post-hit hard total strategy regression case.",
    ),
    "split_eights": Scenario(
        player=["8-Clubs", "8-Diamonds"],
        dealer=["6-Hearts", "Q-Spades"],
        deck=["3-Clubs", "K-Hearts", "2-Diamonds", "9-Spades", "10-Clubs"],
        description="Split-hand layout and active-hand flow.",
    ),
    "player_blackjack": Scenario(
        player=["A-Spades", "K-Hearts"],
        dealer=["9-Clubs", "7-Diamonds"],
        deck=["5-Clubs"],
        description="Natural blackjack payout path.",
    ),
    "dealer_blackjack": Scenario(
        player=["10-Spades", "9-Hearts"],
        dealer=["A-Clubs", "K-Diamonds"],
        deck=["5-Clubs"],
        description="Dealer natural blackjack loss path.",
    ),
}


def parse_card(card_text: str) -> Card:
    """Parse a compact rank-suit token into a Card instance."""
    token = card_text.strip()
    if not token:
        raise ValueError("Card token cannot be empty.")

    separators = ("-", ":", "/")
    parts = None
    for separator in separators:
        if separator in token:
            parts = [part.strip() for part in token.split(separator, maxsplit=1)]
            break

    if not parts or len(parts) != 2:
        raise ValueError(
            f"Card '{card_text}' must be in 'RANK-SUIT' form, e.g. 'A-Hearts' or '10-S'."
        )

    rank, suit = parts
    normalized_rank = rank.upper()
    valid_ranks = {"A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"}
    if normalized_rank not in valid_ranks:
        raise ValueError(f"Unsupported rank '{rank}'.")

    normalized_suit = SUIT_ALIASES.get(suit.lower())
    if normalized_suit is None:
        raise ValueError(f"Unsupported suit '{suit}'.")

    return Card(normalized_rank, normalized_suit)


def parse_cards(card_list_text: str | None) -> list[Card]:
    """Parse a comma-delimited list of cards."""
    if not card_list_text:
        return []
    return [parse_card(token) for token in card_list_text.split(",") if token.strip()]


def cards_to_text(cards: list[dict] | list[Card]) -> list[str]:
    """Render cards consistently for logs and JSON output."""
    rendered = []
    for card in cards:
        if isinstance(card, dict):
            rendered.append(f"{card['rank']} of {card['suit']}")
        else:
            rendered.append(f"{card.rank} of {card.suit}")
    return rendered


def serialize_cards(cards: list[Card]) -> list[dict]:
    """Convert card instances into JSON-friendly dicts."""
    return [card.serialize() for card in cards]


def scenario_payload(name: str) -> dict:
    """Return a JSON-friendly payload for a named scenario."""
    scenario = SCENARIOS[name]
    return {
        "name": name,
        "description": scenario.description,
        "player": serialize_cards([parse_card(card) for card in scenario.player]),
        "dealer": serialize_cards([parse_card(card) for card in scenario.dealer]),
        "deck": serialize_cards([parse_card(card) for card in scenario.deck]),
        "bet": scenario.bet,
        "bankroll": scenario.bankroll,
    }


def list_scenarios() -> list[dict]:
    """Return all built-in scenarios in a frontend-friendly format."""
    return [scenario_payload(name) for name in sorted(SCENARIOS.keys())]


def build_seeded_game(
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
) -> Game:
    """Build a deterministic game object without touching Flask session state."""
    game = Game(seat_count=1, bankroll=bankroll)
    game.player.hands = [player_cards]
    game.player.hand_bets = [bet]
    game.player.hand_states = ["playing"]
    game.player.hand_results = [None]
    game.player.hand_settled = [False]
    game.player.active_hand_index = active_hand_index
    game.dealer.hand = dealer_cards
    game.deck.cards = list(deck_cards or [])
    game.awaiting_bet = awaiting_bet
    game.round_complete = round_complete
    game.last_result = last_result
    return game
