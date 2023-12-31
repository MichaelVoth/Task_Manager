from flask import Flask  # Import Flask to allow us to create our app
import os
import logging

app = Flask(__name__)    # Create a new instance of the Flask class called "app"

logging.basicConfig(level=logging.DEBUG) # This will set the logging level to DEBUG
app.secret_key = "keep it a secret"

# Assuming your Flask app is initialized as 'app'
app.config.from_pyfile(os.path.join('config', 'config.py'))

# Now you can access the API key in your app as:
OPENWEATHER_API_KEY = app.config['OPENWEATHER_API_KEY']