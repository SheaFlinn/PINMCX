from datetime import datetime
from app.extensions import db

class Market(db.Model):
    __tablename__ = 'market'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    resolution_date = db.Column(db.DateTime, nullable=False)
    resolution_method = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(200))
    domain = db.Column(db.String(50))
    parent_market_id = db.Column(db.Integer, db.ForeignKey('market.id'))
    original_source = db.Column(db.String(200))
    original_headline = db.Column(db.String(200))
    original_date = db.Column(db.DateTime)
    scraped_at = db.Column(db.DateTime)
    refined_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    refined_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    domain_tags = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved = db.Column(db.Boolean, default=False)
    resolved_outcome = db.Column(db.String(3))
    resolved_at = db.Column(db.DateTime)
    yes_pool = db.Column(db.Float, default=1000.0)
    no_pool = db.Column(db.Float, default=1000.0)
    liquidity_pool = db.Column(db.Float, default=2000.0)
    liquidity_provider_shares = db.Column(db.Float, default=1.0)
    liquidity_fee = db.Column(db.Float, default=0.003)
    prediction_deadline = db.Column(db.DateTime, nullable=True, default=lambda: datetime.utcnow())
    resolution_deadline = db.Column(db.DateTime, nullable=True, default=lambda: datetime.utcnow())

    # Relationships
    parent_market = db.relationship('Market', remote_side=[id], back_populates='child_markets')
    child_markets = db.relationship('Market', back_populates='parent_market')
    refiner = db.relationship('User', back_populates='refined_markets')
    predictions = db.relationship('Prediction', back_populates='market', lazy=True)
    events = db.relationship('MarketEvent', back_populates='market', lazy=True)
    liquidity_providers = db.relationship('LiquidityProvider', back_populates='market', lazy=True)

    def __repr__(self):
        return f'<Market {self.id}: {self.title}>'
