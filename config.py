import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(basedir, "mcx_points.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Platform Constants
    MIN_TRADE_SIZE = 10
    MAX_TRADE_SIZE = 10000
    CONTRACT_POOL_CAP = 100000
    ENTRY_FEE_PERCENTAGE = 0.05  # 5% entry fee
    LIQUIDITY_BUFFER_FEE_SHARE = 0.01  # 1% goes to LB
    PLATFORM_FEE_SHARE = 0.01  # 1% to platform wallet

    # XP thresholds
    XP_THRESHOLDS = [100, 500, 1000]

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
