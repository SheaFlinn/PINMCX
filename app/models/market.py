from app import db
from datetime import datetime
from app.models.market_event import MarketEvent
import json

class Market(db.Model):
    __tablename__ = 'market'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    contract_hash = db.Column(db.String(255), unique=True, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    outcome = db.Column(db.String(10))
    resolved_at = db.Column(db.DateTime)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    liquidity_pool_id = db.Column(db.Integer, db.ForeignKey('liquidity_pools.id'), nullable=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('contract.id'), nullable=True)
    platform_fee = db.Column(db.Float, default=0.05)
    liquidity_fee = db.Column(db.Float, default=0.01)
    status = db.Column(db.String(20), default='open')
    liquidity_provider_shares = db.Column(db.Float, nullable=True)

    creator = db.relationship('User', back_populates='markets')
    predictions = db.relationship('Prediction', back_populates='market', cascade='all, delete-orphan')
    events = db.relationship('MarketEvent', back_populates='market', cascade='all, delete-orphan')
    contract = db.relationship('Contract', back_populates='market', uselist=False)
    liquidity_pool = db.relationship('LiquidityPool', back_populates='markets', uselist=False)

    def __init__(self, title, description, deadline, creator_id, 
                 liquidity_pool_id=None, platform_fee=0.05, liquidity_fee=0.01, status='open'):
        self.title = title
        self.description = description
        self.deadline = deadline
        self.creator_id = creator_id
        self.liquidity_pool_id = liquidity_pool_id
        self.platform_fee = platform_fee
        self.liquidity_fee = liquidity_fee
        self.status = status
        # Generate contract hash from title and deadline
        self.contract_hash = f'market_{title.lower().replace(" ", "_")}_{deadline.isoformat()}'

    def resolve(self, outcome, user_id=None):
        self.outcome = outcome
        self.resolved_at = datetime.utcnow()
        self.status = 'resolved'
        
        # Use the standardized event logging method
        from app.services.points_prediction_engine import PointsPredictionEngine
        MarketEvent.log_market_resolution(self, user_id or self.creator_id, outcome)
        self.award_xp_for_predictions()

    def award_xp_for_predictions(self):
        """Award XP to users with correct predictions"""
        from app.services.points_prediction_engine import PointsPredictionEngine
        for prediction in self.predictions:
            PointsPredictionEngine.award_xp_for_prediction(prediction)

    def __repr__(self):
        return f'<Market {self.id} {self.title}>'
