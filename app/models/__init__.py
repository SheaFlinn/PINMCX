from flask_sqlalchemy import SQLAlchemy

# Import db from extensions
from app.extensions import db

# Core models
from .user import User
from .league import League
from .league_member import LeagueMember
from .badge import Badge
from .user_badge import UserBadge
from .published_contract import PublishedContract
from .market import Market
from .market_event import MarketEvent
from .platform_wallet import PlatformWallet
from .prediction import Prediction
from .news import NewsSource, NewsHeadline
from .liquidity_pool import LiquidityPool
from .liquidity_provider import LiquidityProvider
from .user_ledger import UserLedger
from .amm_market import AMMMarket
from .draft_contract import DraftContract

__all__ = [
    'User',
    'League',
    'LeagueMember',
    'Badge',
    'UserBadge',
        'PublishedContract',
    'Market',
    'MarketEvent',
    'PlatformWallet',
    'Prediction',
    'NewsSource',
    'NewsHeadline',
    'LiquidityPool',
    'LiquidityProvider',
    'UserLedger',
    'AMMMarket',
    'DraftContract',
    'AMMMarket'
]
