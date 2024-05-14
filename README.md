# Blackjack Flask Application

Welcome to the Blackjack Flask Application! This project implements a classic game of Blackjack using Python's Flask framework. Below you will find information on how to set up, run, and contribute to the project.

## Table of Contents

- [Blackjack Flask Application](#blackjack-flask-application)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Game Rules](#game-rules)
    - [Doubling Down](#doubling-down)
    - [Surrender](#surrender)
  - [API Endpoints](#api-endpoints)
  - [Contributing](#contributing)
  - [License](#license)

## Features

- Classic Blackjack gameplay
- Double Down and Surrender options
- Interactive web-based interface
- Real-time game updates

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

## Contributing

We welcome contributions! To contribute, please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature-branch`)
5. Create a new Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
