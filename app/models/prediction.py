from app import db
from datetime import datetime
from app.models.market_event import MarketEvent
from app.models.market import Market

class Prediction(db.Model):
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    outcome = db.Column(db.String(10), nullable=False)
    confidence = db.Column(db.Float, nullable=True)
    stake = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    points_awarded = db.Column(db.Boolean, default=False)
    xp_awarded = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='predictions')
    market = db.relationship('Market', back_populates='predictions')

    def __init__(self, user_id, market_id, outcome, confidence=None, stake=None, timestamp=None):
        self.user_id = user_id
        self.market_id = market_id
        self.outcome = outcome
        self.confidence = confidence
        self.stake = stake
        self.points_awarded = False
        self.xp_awarded = False
        if timestamp:
            self.timestamp = timestamp

        # Log prediction event after relationships are set
        market = Market.query.get(market_id)
        if not market:
            raise ValueError(f"Market with ID {market_id} not found")
        
        event = MarketEvent(
            market_id=market_id,
            user_id=user_id,
            event_type='prediction_created',
            description=f'Prediction created for market "{market.title}"',
            event_data={
                'outcome': outcome,
                'stake': stake,
                'confidence': confidence
            }
        )
        db.session.add(event)
        db.session.commit()

    def __repr__(self):
        return f'<Prediction {self.id}: {self.user_id} -> {self.market_id} ({self.outcome})>'

    def get_outcome_str(self):
        """Return outcome as string for display purposes"""
        return self.outcome or "Pending"

    def get_prediction_type(self):
        """Return prediction type for compatibility with existing code"""
        return 'YES' if self.outcome.upper() == 'YES' else 'NO'

    def is_correct(self) -> bool:
        """
        Check if this prediction was correct based on the market outcome.
        
        Returns:
            bool: True if prediction matches market outcome, False otherwise
        """
        market = Market.query.get(self.market_id)
        if not market or not market.outcome:
            return False
            
        return self.outcome == market.outcome

    @classmethod
    def create_with_event(cls, user_id, market_id, outcome, confidence=None, stake=None, timestamp=None):
        """Create a prediction and return both the prediction and its event"""
        prediction = cls(user_id, market_id, outcome, confidence, stake, timestamp)
        db.session.add(prediction)
        db.session.commit()
        
        # Get the event that was created
        event = MarketEvent.query.filter_by(
            market_id=market_id,
            user_id=user_id,
            event_type='prediction_created'
        ).order_by(MarketEvent.created_at.desc()).first()
        
        return prediction, event
