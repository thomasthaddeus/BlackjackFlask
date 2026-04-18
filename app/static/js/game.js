const gameArea = document.getElementById('gameArea');

if (gameArea) {
  const startUrl = gameArea.dataset.startUrl;
  const betUrl = gameArea.dataset.betUrl;
  const actionUrlBase = `${gameArea.dataset.actionUrlBase}action/`;

  document.getElementById('hitButton').addEventListener('click', () => {
    performAction('hit');
  });

  document.getElementById('standButton').addEventListener('click', () => {
    performAction('stand');
  });

  document.getElementById('doubleDownButton').addEventListener('click', () => {
    performAction('double_down');
  });

  document.getElementById('splitButton').addEventListener('click', () => {
    performAction('split');
  });

  document.getElementById('surrenderButton').addEventListener('click', () => {
    performAction('surrender');
  });

  document.getElementById('betButton').addEventListener('click', () => {
    const bet = document.getElementById('betSlider').value;
    placeBet(bet);
  });

  document.getElementById('newGameButton').addEventListener('click', startNewGame);

  async function performAction(action) {
    try {
      const response = await fetch(`${actionUrlBase}${action}`, { method: 'POST' });
      const data = await response.json();
      if (!response.ok) {
        showError(data.error || 'Action failed.');
        return;
      }
      updateGameState(data);
    } catch (error) {
      showError(error.message);
    }
  }

  async function placeBet(bet) {
    try {
      const response = await fetch(betUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bet })
      });
      const data = await response.json();
      if (!response.ok) {
        showError(data.error || 'Bet failed.');
        return;
      }
      updateGameState(data);
    } catch (error) {
      showError(error.message);
    }
  }

  async function startNewGame() {
    try {
      const response = await fetch(startUrl, { method: 'POST' });
      const data = await response.json();
      if (!response.ok) {
        showError(data.error || 'Could not start a game.');
        return;
      }
      updateGameState(data);
    } catch (error) {
      showError(error.message);
    }
  }

  function updateGameState(data) {
    document.getElementById('playerHand').textContent = data.playerHand;
    document.getElementById('dealerHand').textContent = data.dealerHand;
    document.getElementById('playerValue').textContent = `Value: ${data.playerValue}`;
    document.getElementById('dealerValue').textContent = `Value: ${data.dealerValue}`;
    document.getElementById('bankroll').textContent = data.bankroll;
    document.getElementById('currentBet').textContent = data.currentBet;
    document.getElementById('statusMessages').textContent = data.message;
    document.getElementById('splitButton').disabled = !data.canSplit;
    document.getElementById('roundState').textContent = data.awaitingBet
      ? 'Place a bet to deal the next hand.'
      : 'Hand in progress.';

    const playerHandsSummary = document.getElementById('playerHandsSummary');
    if (playerHandsSummary && Array.isArray(data.playerHands)) {
      playerHandsSummary.innerHTML = data.playerHands
        .map((hand) => {
          const activeText = hand.isActive ? ' (active)' : '';
          return `<div>${hand.label}${activeText}: ${hand.cards} | Value: ${hand.value} | Bet: ${hand.bet}</div>`;
        })
        .join('');
    }
  }

  function showError(error) {
    console.error('Error:', error);
    document.getElementById('statusMessages').textContent = error || 'Error occurred.';
  }
}
