Usage
=====

Once the application is running, you can start playing Blackjack by visiting ``http://127.0.0.1:5001`` in your browser.

Game Controls:
- **Hit:** Draws a card.
- **Stand:** Ends the player's turn.
- **Double Down:** Doubles the bet and draws one final card.
- **Split:** Splits the hand if possible.
- **Surrender:** Surrenders the hand.
- **New Game:** Resets the table while preserving the bankroll.

Betting:
- Use the bet slider to adjust the bet amount before a round begins.
- Click "Place Bet" to deal a fresh hand and start the round.
- You cannot place another bet until the current round is complete.

Game Status:
- The player hand is displayed after a bet is placed.
- The dealer's hole card stays hidden until the round is resolved.
- Split hands are shown with their own value and bet summary.
- Status messages provide updates on game actions and results.

Developer Workflow:
- Install dependencies with ``poetry install``.
- Run the app with ``poetry run python run.py``.
- Run tests with ``poetry run pytest -q``.
- Build docs with ``poetry run sphinx-build -b html docs/source docs/_build``.
