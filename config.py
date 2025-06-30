import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'mcx_points.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Trade Configurations
    ENTRY_FEE_PERCENTAGE = 0.05
    LIQUIDITY_REWARD_PERCENTAGE = 0.01
    LIQUIDITY_BUFFER_YIELD_ANNUAL = 0.06
    MIN_TRADE_SIZE = 10
    MAX_TRADE_SIZE = 1000
    CONTRACT_POOL_CAP = 250000

    # Other
    NEWS_SCRAPE_INTERVAL_MINUTES = 60
    MARKET_DROP_INTERVAL_HOURS = 12

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
