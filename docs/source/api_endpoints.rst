API Endpoints
=============

The application currently exposes these gameplay endpoints:

- ``POST /blackjack/start``: Reset the game while preserving the player's bankroll.
- ``POST /blackjack/bet``: Place a bet and deal a fresh hand.
- ``GET /blackjack/game_status``: Render the current game status page.
- ``POST /blackjack/action/hit``: Draw a card for the active hand.
- ``POST /blackjack/action/stand``: End play for the active hand.
- ``POST /blackjack/action/double_down``: Double the active hand when allowed.
- ``POST /blackjack/action/split``: Split the active hand when allowed.
- ``POST /blackjack/action/surrender``: Surrender the active hand.

Gameplay actions return JSON. Page-rendering routes return HTML.
