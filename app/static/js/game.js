document.getElementById('hitButton').addEventListener('click', () => {
  performAction('hit');
});

document.getElementById('standButton').addEventListener('click', () => {
  performAction('stand');
});

document.getElementById('doubleDownButton').addEventListener('click', () => {
  performAction('doubleDown');
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

function performAction(action) {
  fetch(`/action/${action}`, { method: 'POST' })
      .then(response => response.json())
      .then(updateGameState)
      .catch(showError);
}

function placeBet(bet) {
  fetch(`/bet`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bet })
  })
      .then(response => response.json())
      .then(updateGameState)
      .catch(showError);
}

function startNewGame() {
  fetch(`/start`, { method: 'POST' })
      .then(response => response.json())
      .then(updateGameState)
      .catch(showError);
}

function updateGameState(data) {
  document.getElementById('playerHand').innerHTML = data.playerHand;
  document.getElementById('dealerHand').innerHTML = data.dealerHand;
  document.getElementById('statusMessages').innerHTML = data.message;
}

function showError(error) {
  console.error('Error:', error);
  document.getElementById('statusMessages').textContent = 'Error occurred.';
}
