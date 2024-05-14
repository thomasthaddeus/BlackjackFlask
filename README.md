# Blackjack Flask Application

Welcome to the Blackjack Flask Application! This project implements a classic game of Blackjack using Python's Flask framework. Below you will find information on how to set up, run, and contribute to the project.

## Overview

The Blackjack Flask Application is a web-based implementation of the classic Blackjack game, built using Python's Flask framework. This project allows users to play Blackjack against a virtual dealer with features such as hit, stand, double down, and surrender.

## Table of Contents

- [Blackjack Flask Application](#blackjack-flask-application)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Game Rules](#game-rules)
    - [Doubling Down](#doubling-down)
    - [Surrender](#surrender)
  - [API Endpoints](#api-endpoints)
    - [Getting Started](#getting-started)
    - [Documentation](#documentation)
  - [Contributing](#contributing)
  - [License](#license)

## Features

- **Classic Blackjack Gameplay:** Experience traditional Blackjack with standard rules.
- **Double Down and Surrender:** Implemented game mechanics for doubling down and surrendering.
- **Interactive Web Interface:** User-friendly interface with real-time updates using JavaScript and Bootstrap.
- **Game State Persistence:** MongoDB integration for tracking user games and state persistence.
- **API Endpoints:** RESTful API for game actions and state management.

## Installation

To get started with the Blackjack Flask application, follow these steps:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/thomasthaddeus/BlackjackFlask.git
   cd BlackjackFlask
   ```

2. **Set up a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MongoDB:**
   Ensure MongoDB is installed and running. Update the MongoDB connection string in the configuration file.

5. **Run the application:**

   ```bash
   flask run
   ```

## Usage

After running the application, open your browser and navigate to `http://127.0.0.1:5000` to start playing Blackjack.

## Game Rules

### Doubling Down

- Allowed when the cards total 9, 10, or 11 without an ace, or when the cards total 16, 17, or 18 with an ace.

### Surrender

- **Early Surrender:** Available before the dealer checks for blackjack.
- **Late Surrender:** Available after the dealer checks for blackjack.
- **When to Surrender:**
  - Surrender with a hard 16 against a dealer's 9, 10, or ace (except two 8s).
  - Surrender with a hard 15 against a dealer's 10.

## API Endpoints

- `GET /api/start`: Starts a new game
- `POST /api/hit`: Draws a card
- `POST /api/stand`: Ends the player's turn
- `POST /api/double`: Doubles the bet and draws one final card
- `POST /api/surrender`: Surrenders the hand

### Getting Started

To set up and run the application locally, follow the detailed instructions provided in the [Installation](docs/source/installation.rst) section of the documentation.

### Documentation

Comprehensive documentation is available, covering all aspects of the application, including setup, usage, game rules, and API endpoints. Visit the [Documentation](https://your-readthedocs-url) to learn more.

## Contributing

We welcome contributions from the community. Please see the [Contributing](docs/source/contributing.rst) section for guidelines on how to contribute to the project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
