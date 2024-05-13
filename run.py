"""run.py
Launch the Flask application using environment-specific configurations.

This script initializes the Flask application using configuration settings
determined by the FLASK_CONFIG environment variable. If FLASK_CONFIG is not
set, it defaults to 'DevelopmentConfig' which is suited for development
environments. The script checks if it's being run as the main module, and if
so, starts the Flask application.
"""

import os
from app import create_app

# Fetch the configuration name from the environment variable or default to 'DevelopmentConfig'
config_name = os.getenv('FLASK_CONFIG', 'DevConfig')
app = create_app(config_name)

if __name__ == "__main__":
    # Production server settings could include:
    # - Turning off debug mode
    # - Configuring a proper host and port
    # - Setting up logging for production
    if app.config['DEBUG'] is False:
        # Production mode specific settings
        app.run(host='0.0.0.0', port=os.getenv('PORT'), debug=False)
    else:
        # Development or Testing mode settings
        app.run(host='127.0.0.1', port=os.getenv('PORT'), debug=True)
