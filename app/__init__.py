from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from app.extensions import db, login_manager, migrate

def create_app(config=None):
    app = Flask(__name__)
    
    # Load default config
    app.config.from_object('config.Config')
    
    # Override with provided config if any
    if config:
        app.config.update(config)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Import models *after* init_app to bind correctly
    from app import models

    # Debug print to confirm tables now bound
    with app.app_context():
        print("Registered tables after init_app:", db.metadata.tables.keys())

    # Register blueprints
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.admin_routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix="/admin")

    from app.admin_api import admin_api as admin_api_blueprint
    app.register_blueprint(admin_api_blueprint)

    return app
