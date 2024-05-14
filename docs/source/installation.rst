Installation
============

Follow these steps to set up and run the Blackjack Flask application:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/thomasthaddeus/BlackjackFlask.git
   cd BlackjackFlask
   ```

2. **Set up a virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MongoDB**:

Ensure MongoDB is installed and running. Update the MongoDB connection string in the configuration file.

5. **Run the application**:

   ```bash
   flask run
   ```

After running the application, open your browser and navigate to <http://127.0.0.1:5000> to start playing Blackjack.
