#!/bin/bash

# Base project directory
PROJECT_DIR=blackjack-flask-app

# Create directories
echo "Creating project structure..."
mkdir -p $PROJECT_DIR/app/blackjack
mkdir -p $PROJECT_DIR/app/static/css
mkdir -p $PROJECT_DIR/app/static/js
mkdir -p $PROJECT_DIR/app/static/images/cards
mkdir -p $PROJECT_DIR/app/templates

# Create Python files
echo "Creating Python files..."
touch $PROJECT_DIR/app/__init__.py
touch $PROJECT_DIR/app/blackjack/__init__.py
touch $PROJECT_DIR/app/blackjack/routes.py
touch $PROJECT_DIR/app/blackjack/models.py
echo "from flask import Flask" > $PROJECT_DIR/run.py
echo "app = Flask(__name__)" >> $PROJECT_DIR/run.py
echo "if __name__ == '__main__':" >> $PROJECT_DIR/run.py
echo "    app.run(debug=True)" >> $PROJECT_DIR/run.py

# Create config file
echo "import os" > $PROJECT_DIR/config.py
echo "class Config:" >> $PROJECT_DIR/config.py
echo "    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')" >> $PROJECT_DIR/config.py

# Create CSS and JavaScript files
touch $PROJECT_DIR/app/static/css/style.css
touch $PROJECT_DIR/app/static/js/game.js

# Create base HTML template
echo "<!DOCTYPE html>" > $PROJECT_DIR/app/templates/base.html
echo "<html lang='en'>" >> $PROJECT_DIR/app/templates/base.html
echo "<head>" >> $PROJECT_DIR/app/templates/base.html
echo "    <meta charset='UTF-8'>" >> $PROJECT_DIR/app/templates/base.html
echo "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>" >> $PROJECT_DIR/app/templates/base.html
echo "    <title>Blackjack Game</title>" >> $PROJECT_DIR/app/templates/base.html
echo "    <link rel='stylesheet' href='{{ url_for('static', filename='css/style.css') }}'>" >> $PROJECT_DIR/app/templates/base.html
echo "</head>" >> $PROJECT_DIR/app/templates/base.html
echo "<body>" >> $PROJECT_DIR/app/templates/base.html
echo "    {% block content %}{% endblock %}" >> $PROJECT_DIR/app/templates/base.html
echo "</body>" >> $PROJECT_DIR/app/templates/base.html
echo "</html>" >> $PROJECT_DIR/app/templates/base.html

# Other files
touch $PROJECT_DIR/requirements.txt
echo "Flask" > $PROJECT_DIR/requirements.txt
echo "Flask-Session" >> $PROJECT_DIR/requirements.txt
touch $PROJECT_DIR/README.md
echo "# Blackjack Flask App" > $PROJECT_DIR/README.md
echo "This is a Flask application for playing blackjack." >> $PROJECT_DIR/README.md
touch $PROJECT_DIR/.gitignore
echo "venv/" > $PROJECT_DIR/.gitignore
echo "__pycache__/" >> $PROJECT_DIR/.gitignore
echo "*.pyc" >> $PROJECT_DIR/.gitignore

echo "Project setup complete."
