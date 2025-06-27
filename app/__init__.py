import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin
from config import Config, TestingConfig
from app.extensions import db
from app.models import User

migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name=None):
    app = Flask(__name__, static_folder=os.path.join(os.getcwd(), "static"))

    if config_name == "testing":
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Set up user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        from . import models  # Register models
        if config_name == "testing":
            db.create_all()  # Create tables only for testing
            
        # Register routes
        from .routes import main
        app.register_blueprint(main)

    return app
