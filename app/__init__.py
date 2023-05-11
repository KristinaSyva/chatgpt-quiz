from flask import Flask, render_template, jsonify, request
import os
import openai
import aiapi
from dotenv import load_dotenv

from .routes import main
from .config import config
from .models import GameQuestions, GameAnswers, Quiz
from .extensions import db

def create_app():
    app = Flask(__name__)

    # Load the configuration settings
    config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])

    db.init_app(app)
    
    # Register the blueprints
    app.register_blueprint(main)

    # Load the environment variables
    load_dotenv()

    return app

