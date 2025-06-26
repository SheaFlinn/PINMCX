import os

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///mcx.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Market configuration
    CONTRACT_POOL_CAP = 10000  # Maximum total points in a market (YES + NO pools)
    
    # AMM configuration
    AMM_LIQUIDITY_FEE = 0.003  # 0.3% fee on trades
    
    # League configuration
    LEAGUE_UPDATE_INTERVAL = 7  # Days between league updates
    BADGE_AWARD_INTERVAL = 1    # Days between badge awards
    
    # Trading configuration
    MIN_TRADE_SIZE = 1          # Minimum points for a trade
    MAX_TRADE_SIZE = 1000       # Maximum points for a trade
    
    # Prediction configuration
    MIN_PREDICTION_POINTS = 1   # Minimum points for a prediction
    MAX_PREDICTION_POINTS = 1000 # Maximum points for a prediction
    
    # Market resolution configuration
    RESOLUTION_BUFFER_DAYS = 7   # Days after market end before resolution
    
    # Email configuration (for future use)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['admin@example.com']
<<<<<<< HEAD

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
=======
>>>>>>> d745d5f (Fix badge image rendering and static path config)
