# Blackjack Flask Application

This repository contains a browser-based Blackjack game built with Flask, a JavaScript front end, and a Poetry-first developer workflow. The current iteration focuses on a polished table UI, multi-seat play from one bankroll, deterministic devtools, and runtime logging through Loguru.

## Overview

The app supports a full round-based Blackjack flow against a dealer, including:

- Multi-seat table setup with up to 7 occupied seats from a single bankroll
- A persistent multi-deck shoe
- Hit, stand, double down, split, and surrender actions
- Basic-strategy guidance shown in the sidebar and updated during play
- Session-backed game state so the active table survives across requests
- Front-end and CLI devtools for seeding exact hands and scenarios
- Poetry-based setup for local development, tests, docs, and CI

## Installation

1. Clone the repository.

```bash
git clone https://github.com/thomasthaddeus/BlackjackFlask.git
cd BlackjackFlask
```

2. Install dependencies with Poetry.

```bash
poetry install --with dev,docs
```

3. Run the development server.

```bash
poetry run python run.py
```

4. Open the app at `http://127.0.0.1:5001`.

## Runtime Configuration

The application reads configuration from environment variables and `FLASK_CONFIG`.

Common options:

- `FLASK_CONFIG=DevelopmentConfig|TestingConfig|ProductionConfig`
- `PORT=5001`
- `BLACKJACK_LOG_LEVEL=TRACE|DEBUG|INFO|SUCCESS|WARNING|ERROR|CRITICAL`
- `BLACKJACK_LOG_SINK` to override the log file path
- `BLACKJACK_LOG_RETENTION=14` to control how many rotated logs to keep
- `BLACKJACK_LOG_TO_CONSOLE=1` to keep console logging enabled
- `BLACKJACK_DEVTOOLS=1` to enable the browser overlay outside testing and development defaults

Example:

```bash
poetry run python run.py --log-level DEBUG
```

By default, logs are written under `logs/` using timestamped filenames like `logs/blackjack-YYYYMMDDHHMMSS.log`, rotated daily or at roughly 10 MB, with a fixed retention window.

## Gameplay Flow

When the player first enters the game, the app opens a seat-selection modal. From there the user chooses how many seats to play from the shared bankroll.

During play:

- The dealer hand stays centered at the top of the table
- Up to 7 seat positions render around the semicircle
- The active seat is highlighted directly on the table
- The active seat's hands render in the large player area
- Betting, strategy guidance, and table status appear in the right sidebar

## Developer Workflow

Install dependencies:

```bash
poetry install --with dev,docs
```

Run tests:

```bash
poetry run pytest -q
```

Build documentation:

```bash
poetry run sphinx-build -b html docs/source docs/_build
```

Run the CLI devtools harness:

```bash
poetry run python -m app.tools.devtools --scenario split_eights --action hit --action stand --log-level DEBUG
```

## API Endpoints

Primary gameplay routes:

- `GET /blackjack/`
- `POST /blackjack/start`
- `POST /blackjack/bet`
- `GET /blackjack/game_status`
- `POST /blackjack/action/<action>`
- `POST /blackjack/double_down`
- `POST /blackjack/split`

Developer-only routes when devtools are enabled:

- `GET /blackjack/devtools/options`
- `POST /blackjack/devtools/seed`

## Documentation

Sphinx source files live under `docs/source`. The generated HTML output can be built locally with Poetry:

```bash
poetry run sphinx-build -b html docs/source docs/_build
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
