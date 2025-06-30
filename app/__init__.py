import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_admin import Admin
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_apscheduler import APScheduler

from config import Config, TestingConfig
from app.extensions import db, migrate, login_manager, mail, admin, cors, jwt, socketio, scheduler

def create_app(config_name=None):
    app = Flask(__name__, static_folder=os.path.join(os.getcwd(), "static"))

    if config_name == "testing":
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    admin.init_app(app)
    cors.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)
    scheduler.init_app(app)
    scheduler.start()

    # Set up user loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.market import bp as market_bp
    app.register_blueprint(market_bp)

    from app.predictions import bp as predictions_bp
    app.register_blueprint(predictions_bp)

    from app.liquidity import bp as liquidity_bp
    app.register_blueprint(liquidity_bp)

    from app.xp import bp as xp_bp
    app.register_blueprint(xp_bp)

    from app.amm import bp as amm_bp
    app.register_blueprint(amm_bp)

    # Initialize admin views
    from app.models import User, Market, Prediction, MarketEvent, PlatformWallet, Badge, UserBadge
    from flask_admin.contrib.sqla import ModelView
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Market, db.session))
    admin.add_view(ModelView(Prediction, db.session))
    admin.add_view(ModelView(MarketEvent, db.session))
    admin.add_view(ModelView(PlatformWallet, db.session))
    admin.add_view(ModelView(Badge, db.session))
    admin.add_view(ModelView(UserBadge, db.session))

    # Initialize services
    from app.services import liquidity_service, xp_service, admin_service, amm_service
    liquidity_service.init_app(app)
    xp_service.init_app(app)
    admin_service.init_app(app)
    amm_service.init_app(app)

    # Register CLI commands
    from app.commands import init_db, create_admin, seed_data
    app.cli.add_command(init_db)
    app.cli.add_command(create_admin)
    app.cli.add_command(seed_data)

    # Register models
    with app.app_context():
        from . import models
        if config_name == "testing":
            db.create_all()

    return app
