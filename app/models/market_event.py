# app/models/market_event.py

from app import db
from datetime import datetime

class MarketEvent(db.Model):
    __tablename__ = 'market_events'

    id = db.Column(db.Integer, primary_key=True)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), nullable=False)
    event_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    market = db.relationship('Market', back_populates='events')

    @classmethod
    def log_market_creation(cls, market, user_id):
        """Log the creation of a new market"""
        event = cls(
            market_id=market.id,
            user_id=user_id,
            event_type='market_created',
            description=f'Market "{market.title}" created',
            event_data={
                'title': market.title,
                'description': market.description,
                'deadline': str(market.deadline),
                'platform_fee': str(market.platform_fee) if market.platform_fee else "0.0",
                'liquidity_fee': str(market.liquidity_fee) if market.liquidity_fee else "0.0"
            }
        )
        db.session.add(event)
        db.session.commit()
        return event

    @classmethod
    def log_prediction(cls, market, user_id, stake, outcome):
        """Log a prediction event for a market"""
        event = cls(
            market_id=market.id,
            user_id=user_id,
            event_type='prediction_created',
            description=f'Prediction created for market "{market.title}"',
            event_data={
                'outcome': outcome,
                'stake': stake,
                'confidence': 1.0  # Default confidence for now
            }
        )
        db.session.add(event)
        db.session.commit()
        return event

    @classmethod
    def log_market_resolution(cls, market, user_id, outcome):
        """Log market resolution event"""
        event = cls(
            market_id=market.id,
            user_id=user_id,
            event_type='market_resolved',
            description=f'Market "{market.title}" resolved to {outcome}',
            event_data={
                'outcome': outcome,
                'resolved_at': str(datetime.utcnow()),
                'lineage': getattr(market, 'lineage', None)
            }
        )
        db.session.add(event)
        db.session.commit()
        return event

    def __repr__(self):
        return f'<MarketEvent {self.id}: {self.event_type} for Market {self.market_id}>'