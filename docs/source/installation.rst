Installation
============

Follow these steps to set up and run the Blackjack Flask application:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/thomasthaddeus/BlackjackFlask.git
   cd BlackjackFlask
   ```

2. **Install Poetry** if it is not already available.

3. **Install the required dependencies**:

   ```bash
   poetry install
   ```

4. **Run the application**:

   ```bash
   poetry run python run.py
   ```

   To enable runtime logging::

      poetry run python run.py --log-level INFO

After running the application, open your browser and navigate to <http://127.0.0.1:5001> to start playing Blackjack.
