import os
import logging
from flask import Flask
from flask_login import current_user, LoginManager, UserMixin
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config, TestingConfig
from app.extensions import db, login_manager, migrate
from app import models

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add file handler for logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'mcx_points.log')
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

@login_manager.user_loader
def load_user(id):
    from .models import User
    return User.query.get(int(id))

def create_app(config_name=None):
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.debug = True  # Enable debug mode
    app.config['SECRET_KEY'] = 'your-secret-key-here'

    if config_name == "testing":
        app.config.from_object(TestingConfig)
    else:
        db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'mcx_points.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    # Register CLI commands if present
    try:
        from .commands import register_commands
        register_commands(app)
    except ImportError:
        pass

    # Register blueprints
    from .routes import main
    try:
        from . import admin  # Import the admin blueprint
        app.register_blueprint(admin.admin)  # Register the admin blueprint
    except ImportError:
        pass
    app.register_blueprint(main)

    @app.before_request
    def before_request():
        """Update user streaks and last active time"""
        if current_user.is_authenticated:
            # Update last active time
            current_user.last_active = datetime.utcnow()
            
            # Update streak
            from app.services import PointsService
            PointsService.update_streak(current_user)
            
            # Award badges based on streak
            if current_user.current_streak >= 5 and not current_user.get_badges():
                current_user.award_badge('daily_streak_5')
            if current_user.current_streak >= 10:
                current_user.award_badge('daily_streak_10')
            if current_user.current_streak >= 30:
                current_user.award_badge('daily_streak_30')
            
            # Commit changes
            db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
>>>>>>> d745d5f (Fix badge image rendering and static path config)
