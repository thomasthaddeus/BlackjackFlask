# blackjack/routes.py

import logging
from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from .models import Game

# Define the blueprint
blackjack_bp = Blueprint('blackjack', __name__)

# Set up basic configuration at the beginning of your file
logging.basicConfig(filename='blackjack.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@blackjack_bp.route('/')
def index():
    return render_template('index.html')

@blackjack_bp.route('/bet', methods=['POST'])
def place_bet():
    bet = request.form.get('bet', type=int)
    try:
        if bet is None or bet < 0:
            logging.warning('Attempt to place invalid bet amount')
            flash('Invalid bet amount. Please enter a valid number.')
            return redirect(url_for('blackjack.index'))
        session['bet'] = bet
        logging.info(f'Bet placed: {bet}')
        return redirect(url_for('blackjack.game_status'))
    except Exception as e:
        logging.error(f'Error placing bet: {str(e)}')
        flash('An error occurred while placing the bet.')
        return redirect(url_for('blackjack.index'))

@blackjack_bp.route('/status')
def game_status():
    try:
        game = session.get('game')
        if not game:
            flash('No active game found. Please start a new game.')
            return redirect(url_for('blackjack.index'))
        player_hand = game.player.hand
        dealer_hand = game.dealer.hand if game.dealer_turn_over else []
        return render_template('status.html', player_hand=player_hand, dealer_hand=dealer_hand)
    except Exception as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for('blackjack.index'))

@blackjack_bp.route('/start', methods=['POST'])
def start_game():
    bet = request.form.get('bet', type=int)
    if bet is None or bet < 0:
        flash('Invalid bet amount. Please enter a valid number.')
        return redirect(url_for('blackjack.index'))
    session['bet'] = bet
    return start_new_round()

@blackjack_bp.route('/hit', methods=['POST'])
def hit():
    if 'game' not in session:
        flash('No game in progress. Please start a new game.')
        return redirect(url_for('blackjack.index'))
    game = session['game']
    game.player.hit(game.deck)
    return redirect(url_for('blackjack.game_status'))
