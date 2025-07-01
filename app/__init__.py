from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from app.extensions import db, login_manager, migrate

# Initialize extensions (moved to extensions.py)

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

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

    return app
