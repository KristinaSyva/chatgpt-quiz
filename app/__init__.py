from flask import Flask
import os
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap
from .config import config
from .models import GameQuestions, GameAnswers, Quiz
from .extensions import db, login_manager
from .cli import create_db, drop_table
from flask_toastr import Toastr


def create_app():
    app = Flask(__name__)

    # Load the configuration settings
    config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])

    app.cli.add_command(create_db)
    app.cli.add_command(drop_table)

    csrf = CSRFProtect(app)
    Toastr(app)
    Bootstrap(app)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = "info"
    
    from app.auth.routes import auth
    from app.main.routes import main
    from app.errors.handlers import errors

    # Register the blueprints
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(errors)

    # Load the environment variables
    load_dotenv()

    return app

