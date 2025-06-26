import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config, TestingConfig
from app.extensions import db

migrate = Migrate()

def create_app(config_name=None):
    app = Flask(__name__, static_folder=os.path.join(os.getcwd(), "static"))

    if config_name == "testing":
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from . import models  # Register models
        if config_name == "testing":
            db.create_all()  # Create tables only for testing

    from . import routes  # Register routes

    return app
