from datetime import datetime
from app.extensions import db

class MarketEvent(db.Model):
    """Model to track important events in a market's lifecycle"""
    id = db.Column(db.Integer, primary_key=True)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    event_type = db.Column(db.String, nullable=False)  # e.g., 'market_created', 'prediction', 'resolved'
    description = db.Column(db.String(200), nullable=False)
    event_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    market = db.relationship('Market', back_populates='events')
    user = db.relationship('User', back_populates='events')

    @staticmethod
    def log_market_creation(market, user_id):
        """Log the creation of a new market"""
        return MarketEvent(
            market_id=market.id,
            event_type='market_created',
            user_id=user_id,
            description=f'Market "{market.title}" created',
            event_data={
                'title': market.title,
                'description': market.description,
                'resolution_date': market.resolution_date.isoformat(),
                'resolution_method': market.resolution_method,
                'domain': market.domain,
                'lineage': market.lineage_chain
            }
        )

    @staticmethod
    def log_prediction(market, user_id, prediction):
        """Log a prediction event"""
        return MarketEvent(
            market_id=market.id,
            event_type='prediction',
            user_id=user_id,
            description=f'User {user_id} predicted on market {market.title}',
            event_data={
                'prediction_id': prediction.id,
                'shares': prediction.shares,
                'outcome': prediction.outcome,
                'xp_awarded': prediction.xp_awarded
            }
        )

    @staticmethod
    def log_market_resolution(market, user_id):
        """Log market resolution"""
        return MarketEvent(
            market_id=market.id,
            event_type='market_resolved',
            user_id=user_id,
            description=f'Market "{market.title}" resolved',
            event_data={
                'outcome': market.resolved_outcome,
                'resolved_at': datetime.utcnow().isoformat(),
                'lineage': market.lineage_chain
            }
        )

    @staticmethod
    def log_prediction_resolution(prediction_id, market_id, user_id, outcome, points_awarded, xp_awarded):
        """Log a prediction resolution event"""
        return MarketEvent(
            market_id=market_id,
            user_id=user_id,
            event_type='prediction_resolved',
            description=f'Prediction {prediction_id} resolved with outcome {outcome}',
            event_data={
                'prediction_id': prediction_id,
                'outcome': outcome,
                'points_awarded': points_awarded,
                'xp_awarded': xp_awarded
            }
        )

    def __repr__(self):
        return f'<MarketEvent {self.id}: {self.event_type} for Market {self.market_id}>'
