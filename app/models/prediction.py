from datetime import datetime
from app.extensions import db

class Prediction(db.Model):
    """Prediction model."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    shares = db.Column(db.Float, nullable=False)
    platform_fee = db.Column(db.Float, nullable=True)  # 5% fee deducted from shares
    outcome = db.Column(db.Boolean, nullable=False)
    used_liquidity_buffer = db.Column(db.Boolean, default=False)  # Track if prediction used LB
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    xp_awarded = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship('User', back_populates='predictions')
    market = db.relationship('Market', back_populates='predictions')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Handle market_id or market object
        market_id = kwargs.get('market_id')
        if not market_id and 'market' in kwargs and kwargs['market']:
            market_id = kwargs['market'].id

        # Handle user_id or user object
        user_id = kwargs.get('user_id')
        if not user_id and 'user' in kwargs and kwargs['user']:
            user_id = kwargs['user'].id

        # Log prediction if we have both market_id and user_id
        if market_id and user_id:
            from app.models.market_event import MarketEvent
            market = db.session.get(kwargs['market'].__class__, market_id)
            if market:
                print(f"Prediction logged for market: {market.title}")
                event = MarketEvent.log_prediction(market, user_id, self)
                db.session.add(event)

    def __repr__(self):
        return f'<Prediction {self.id}: {self.shares} shares on Market {self.market_id}>'
