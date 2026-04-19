const gameArea = document.getElementById('gameArea');

if (gameArea) {
  const startUrl = gameArea.dataset.startUrl;
  const betUrl = gameArea.dataset.betUrl;
  const actionUrlBase = `${gameArea.dataset.actionUrlBase}action/`;
  const seatCountConfigured = Number(gameArea.dataset.seatCount || 0);
  const devtoolsEnabled = gameArea.dataset.devtoolsEnabled === 'true';
  const devtoolsOptionsUrl = gameArea.dataset.devtoolsOptionsUrl;
  const devtoolsSeedUrl = gameArea.dataset.devtoolsSeedUrl;
  const betSlider = document.getElementById('betSlider');
  const betValue = document.getElementById('betValue');
  let devtoolsScenarios = [];

  betSlider?.addEventListener('input', () => {
    betValue.textContent = betSlider.value;
  });

  document.getElementById('hitButton')?.addEventListener('click', () => performAction('hit'));
  document.getElementById('standButton')?.addEventListener('click', () => performAction('stand'));
  document.getElementById('doubleDownButton')?.addEventListener('click', () => performAction('double_down'));
  document.getElementById('splitButton')?.addEventListener('click', () => performAction('split'));
  document.getElementById('surrenderButton')?.addEventListener('click', () => performAction('surrender'));
  document.getElementById('betButton')?.addEventListener('click', () => placeBet(betSlider.value));
  document.getElementById('newGameButton')?.addEventListener('click', () => openSeatSelectionModal());
  document.getElementById('seatSelectionStart')?.addEventListener('click', submitSeatSelection);

  initializeSeatSelection();
  initializeDevtools();

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

  async function startNewGame(seatCount) {
    try {
      const payload = seatCount ? { seatCount: Number(seatCount) } : {};
      const response = await fetch(startUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) {
        showError(data.error || 'Could not start a game.');
        return;
      }
      closeSeatSelectionModal();
      updateGameState(data);
    } catch (error) {
      showError(error.message);
    }
  }

  function updateGameState(data) {
    renderHands(data);
    renderSeatPods(data.seats || [], data.activeSeatIndex);
    renderShoeStatus(data);
    document.getElementById('dealerValue').textContent = `Value: ${data.dealerValue}`;
    document.getElementById('bankroll').textContent = data.bankroll;
    document.getElementById('statusMessages').textContent = data.message;
    document.getElementById('strategyAdvice').textContent = data.strategyAdvice;
    document.getElementById('splitButton').disabled = !data.canSplit;
    document.getElementById('doubleDownButton').disabled = !data.canDoubleDown;
    document.getElementById('surrenderButton').disabled = !data.canSurrender;
    document.getElementById('roundStatePopup').textContent = data.awaitingBet
      ? 'Place a bet to deal the next hand.'
      : `${data.activeSeatLabel || 'Table'} in progress.`;
    betValue.textContent = betSlider.value;
    gameArea.dataset.seatCount = String(data.seatCount || 0);

  }

  function renderHands(data) {
    const game = data.game || {};
    const dealerCards = game.dealer?.hand || [];
    const playerHands = data.playerHands || [];

    renderPlayerHands(document.getElementById('playerHands'), playerHands, game.player?.hands || []);
    renderCardRow(document.getElementById('dealerHand'), dealerCards, !data.roundComplete, false);
  }

  function renderPlayerHands(container, handMetadata, serializedHands) {
    if (!container) {
      return;
    }
    if (!serializedHands.length) {
      container.innerHTML = `
        <div class="split-hand-panel active">
          <div class="split-hand-header">
            <span>Hand 1 (active)</span>
            <span>Value: 0</span>
          </div>
          <div class="card-row">No cards dealt yet.</div>
        </div>
      `;
      return;
    }

    container.innerHTML = serializedHands
      .map((hand, index) => {
        const metadata = handMetadata[index] || {};
        const label = metadata.label || `Hand ${index + 1}`;
        const activeClass = metadata.isActive ? ' active' : '';
        const cardsMarkup = hand.length
          ? hand.map((card) => renderCard(card)).join('')
          : 'No cards dealt yet.';
        return `
          <div class="split-hand-panel${activeClass}">
            <div class="split-hand-header">
              <span>${label}${metadata.isActive ? ' (active)' : ''}</span>
              <span>Value: ${metadata.value ?? 0}</span>
            </div>
            <div class="card-row">${cardsMarkup}</div>
          </div>
        `;
      })
      .join('');
  }

  function renderSeatPods(seats, activeSeatIndex) {
    for (let position = 0; position < 7; position += 1) {
      const spot = document.getElementById(`seatSpot${position}`);
      if (!spot) {
        continue;
      }
      const seat = seats.find((item) => item.position === position);
      if (!seat || !seat.occupied) {
        spot.innerHTML = '<div class="seat-pod seat-pod--empty"></div>';
        continue;
      }

      const handMarkup = (seat.hands || [])
        .map((hand, index) => renderCompactHand(hand, index === 0 && seat.isActive))
        .join('');
      spot.innerHTML = `
        <div class="seat-pod${seat.isActive ? ' seat-pod--active' : ''}">
          <div class="seat-pod__meta">
            <span class="seat-pod__label">${seat.label}</span>
            <span class="seat-pod__bet">$${seat.bet}</span>
          </div>
          <div class="seat-pod__hands">${handMarkup || '<div class="seat-pod__empty">Waiting</div>'}</div>
        </div>
      `;
    }
  }

  function renderCompactHand(hand, emphasize) {
    const rows = [];
    const cards = hand.cards || [];
    for (let index = 0; index < cards.length; index += 4) {
      rows.push(cards.slice(index, index + 4));
    }
    const rowMarkup = rows
      .map((row) => `
        <div class="compact-card-row">
          ${row.map((card, index) => renderCompactCard(card, index)).join('')}
        </div>
      `)
      .join('');

    return `
      <div class="compact-hand${emphasize ? ' compact-hand--active' : ''}">
        <div class="compact-hand__value">${hand.value || ''}</div>
        <div class="compact-card-stack">${rowMarkup}</div>
      </div>
    `;
  }

  function renderShoeStatus(data) {
    const shoeStatus = document.getElementById('shoeStatus');
    if (shoeStatus) {
      shoeStatus.textContent = `Shoe: ${data.shoeRemaining} cards remaining (${data.shoeDecks} decks)`;
    }
  }

  function renderCardRow(container, cards, hideHoleCard, compact) {
    if (!cards.length) {
      container.textContent = 'No cards dealt yet.';
      return;
    }

    container.innerHTML = cards
      .map((card, index) => {
        if (hideHoleCard && index > 0) {
          return `<div class="${compact ? 'compact-card-hidden' : 'card-hidden'}" aria-label="Hidden card"></div>`;
        }
        return compact ? renderCompactCard(card, index) : renderCard(card);
      })
      .join('');
  }

  function renderCard(card) {
    const suitSymbol = getSuitSymbol(card.suit);
    const colorClass = isRedSuit(card.suit) ? 'red' : 'black';
    return `
      <div class="playing-card ${colorClass}" aria-label="${card.rank} of ${card.suit}">
        <div class="card-corner top">
          <span>${card.rank}</span>
          <span>${suitSymbol}</span>
        </div>
        <div class="card-center">${suitSymbol}</div>
        <div class="card-corner bottom">
          <span>${card.rank}</span>
          <span>${suitSymbol}</span>
        </div>
      </div>
    `;
  }

  function renderCompactCard(card, stackIndex) {
    const suitSymbol = getSuitSymbol(card.suit);
    const colorClass = isRedSuit(card.suit) ? 'red' : 'black';
    return `
      <div class="compact-card ${colorClass}" style="--stack-index:${stackIndex}" aria-label="${card.rank} of ${card.suit}">
        <div class="compact-card-corner top">
          <span>${card.rank}</span>
          <span>${suitSymbol}</span>
        </div>
        <div class="compact-card-center">${suitSymbol}</div>
        <div class="compact-card-corner bottom">
          <span>${card.rank}</span>
          <span>${suitSymbol}</span>
        </div>
      </div>
    `;
  }

  function getSuitSymbol(suit) {
    const suits = {
      Hearts: '♥',
      Diamonds: '♦',
      Clubs: '♣',
      Spades: '♠'
    };
    return suits[suit] || '?';
  }

  function isRedSuit(suit) {
    return suit === 'Hearts' || suit === 'Diamonds';
  }

  function showError(error) {
    console.error('Error:', error);
    document.getElementById('statusMessages').textContent = error || 'Error occurred.';
  }

  function initializeSeatSelection() {
    if (!seatCountConfigured) {
      openSeatSelectionModal();
    }
  }

  function openSeatSelectionModal() {
    const modal = document.getElementById('seatSelectionModal');
    if (modal) {
      modal.hidden = false;
    }
  }

  function closeSeatSelectionModal() {
    const modal = document.getElementById('seatSelectionModal');
    if (modal) {
      modal.hidden = true;
    }
  }

  function submitSeatSelection() {
    const seatCount = document.getElementById('seatCountSelect')?.value || '1';
    startNewGame(seatCount);
  }

  async function initializeDevtools() {
    if (!devtoolsEnabled) {
      return;
    }

    const toggle = document.getElementById('devtoolsToggle');
    const overlay = document.getElementById('devtoolsOverlay');
    const closeButton = document.getElementById('devtoolsClose');
    const applyButton = document.getElementById('devtoolsApply');
    const resetButton = document.getElementById('devtoolsReset');
    const scenarioSelect = document.getElementById('devtoolsScenario');

    toggle?.addEventListener('click', () => setDevtoolsVisibility(!(overlay && !overlay.hidden)));
    closeButton?.addEventListener('click', () => setDevtoolsVisibility(false));
    applyButton?.addEventListener('click', applyDevtoolsSeed);
    resetButton?.addEventListener('click', resetDevtoolsForm);
    scenarioSelect?.addEventListener('change', handleScenarioChange);

    document.addEventListener('keydown', (event) => {
      if (event.key === 'F9') {
        event.preventDefault();
        setDevtoolsVisibility(!(overlay && !overlay.hidden));
      }
      if (event.key === 'Escape' && overlay && !overlay.hidden) {
        setDevtoolsVisibility(false);
      }
    });

    try {
      const response = await fetch(devtoolsOptionsUrl);
      const data = await response.json();
      if (!response.ok) {
        setDevtoolsStatus(data.error || 'Could not load devtools scenarios.');
        return;
      }
      devtoolsScenarios = data.scenarios || [];
      populateScenarioOptions(devtoolsScenarios);
      if (overlay) {
        overlay.hidden = true;
      }
    } catch (error) {
      setDevtoolsStatus(error.message);
    }

    function setDevtoolsVisibility(isVisible) {
      if (!overlay || !toggle) {
        return;
      }
      overlay.hidden = !isVisible;
      toggle.setAttribute('aria-expanded', String(isVisible));
    }
  }

  function populateScenarioOptions(scenarios) {
    const scenarioSelect = document.getElementById('devtoolsScenario');
    if (!scenarioSelect) {
      return;
    }
    scenarioSelect.innerHTML = '<option value="">Custom hand</option>';
    scenarios.forEach((scenario) => {
      const option = document.createElement('option');
      option.value = scenario.name;
      option.textContent = `${scenario.name.replace(/_/g, ' ')}${scenario.description ? ` - ${scenario.description}` : ''}`;
      scenarioSelect.appendChild(option);
    });
  }

  function handleScenarioChange(event) {
    const scenario = devtoolsScenarios.find((item) => item.name === event.target.value);
    if (!scenario) {
      return;
    }
    document.getElementById('devtoolsPlayer').value = serializeCardsForInput(scenario.player);
    document.getElementById('devtoolsDealer').value = serializeCardsForInput(scenario.dealer);
    document.getElementById('devtoolsDeck').value = serializeCardsForInput(scenario.deck);
    document.getElementById('devtoolsBet').value = scenario.bet;
    document.getElementById('devtoolsBankroll').value = scenario.bankroll;
    document.getElementById('devtoolsAwaitingBet').value = 'false';
    document.getElementById('devtoolsRoundComplete').value = 'false';
    document.getElementById('devtoolsLastResult').value = '';
    setDevtoolsStatus(`Loaded scenario: ${scenario.name}`);
  }

  function serializeCardsForInput(cards) {
    return (cards || []).map((card) => `${card.rank}-${card.suit}`).join(',');
  }

  function resetDevtoolsForm() {
    const ids = [
      'devtoolsScenario',
      'devtoolsPlayer',
      'devtoolsDealer',
      'devtoolsDeck',
      'devtoolsBet',
      'devtoolsBankroll',
      'devtoolsAwaitingBet',
      'devtoolsRoundComplete',
      'devtoolsLastResult'
    ];
    ids.forEach((id) => {
      const element = document.getElementById(id);
      if (!element) {
        return;
      }
      if (id === 'devtoolsScenario') {
        element.value = '';
      } else if (id === 'devtoolsBet') {
        element.value = 100;
      } else if (id === 'devtoolsBankroll') {
        element.value = 1000;
      } else if (id === 'devtoolsAwaitingBet' || id === 'devtoolsRoundComplete') {
        element.value = 'false';
      } else {
        element.value = '';
      }
    });
    setDevtoolsStatus('Devtools form reset.');
  }

  async function applyDevtoolsSeed() {
    const payload = {
      scenario: document.getElementById('devtoolsScenario')?.value || '',
      player: document.getElementById('devtoolsPlayer')?.value || '',
      dealer: document.getElementById('devtoolsDealer')?.value || '',
      deck: document.getElementById('devtoolsDeck')?.value || '',
      bet: Number(document.getElementById('devtoolsBet')?.value || 100),
      bankroll: Number(document.getElementById('devtoolsBankroll')?.value || 1000),
      awaitingBet: document.getElementById('devtoolsAwaitingBet')?.value === 'true',
      roundComplete: document.getElementById('devtoolsRoundComplete')?.value === 'true',
      lastResult: document.getElementById('devtoolsLastResult')?.value || ''
    };

    try {
      const response = await fetch(devtoolsSeedUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) {
        setDevtoolsStatus(data.error || 'Could not apply devtools state.');
        return;
      }
      updateGameState(data);
      setDevtoolsStatus(data.message || 'Devtools state applied.');
    } catch (error) {
      setDevtoolsStatus(error.message);
    }
  }

  function setDevtoolsStatus(message) {
    const status = document.getElementById('devtoolsStatus');
    if (status) {
      status.textContent = message;
    }
  }
}
