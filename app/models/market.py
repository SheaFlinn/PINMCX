from datetime import datetime
from app.extensions import db
from app.models.market_event import MarketEvent

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
    liquidity_providers = db.relationship("LiquidityProvider", back_populates="market", lazy=True)
    market_liquidity_pool = db.relationship('LiquidityPool', back_populates='market', uselist=False)

    def __repr__(self):
        return f'<Market {self.id}: {self.title}>'

    def award_xp_for_predictions(self):
        """
        Award XP to users based on their predictions for this market.
        Only awards XP once per prediction (tracks via xp_awarded flag).
        """
        from app.services.xp_service import XPService
        from app.models.market_event import MarketEvent
        
        for prediction in self.predictions:
            if prediction.xp_awarded:
                continue  # Skip if XP already awarded
            
            # Determine if prediction was correct
            success = (prediction.outcome == (self.resolved_outcome == 'YES'))
            
            # Award XP
            XPService.award_prediction_xp(prediction.user, success=success)
            
            # Mark prediction as XP awarded
            prediction.xp_awarded = True
            
            # Log the XP award event
            event = MarketEvent(
                market_id=self.id,
                user_id=prediction.user_id,
                event_type='xp_awarded',
                description=f'XP awarded for prediction on market {self.title}',
                event_data={
                    'prediction_id': prediction.id,
                    'success': success,
                    'xp_awarded': True
                }
            )
            db.session.add(event)
            
        # Commit XP awards and events
        db.session.commit()

    def resolve(self, outcome: str) -> None:
        """
        Resolve the market with the given outcome.
        
        Args:
            outcome: 'YES' or 'NO'
            
        Raises:
            ValueError: If market is already resolved or outcome is invalid
        """
        if self.resolved:
            raise ValueError(f"Market {self.id} is already resolved")
            
        if outcome not in ['YES', 'NO']:
            raise ValueError(f"Invalid outcome: {outcome}. Must be 'YES' or 'NO'")
            
        self.resolved = True
        self.resolved_outcome = outcome
        self.resolved_at = datetime.utcnow()
        
        # Award XP for all predictions
        self.award_xp_for_predictions()
        
        # Log resolution event
        event = MarketEvent(
            market_id=self.id,
            event_type='market_resolved',
            description=f'Market "{self.title}" resolved with outcome {outcome}',
            event_data={
                'outcome': outcome,
                'resolved_at': self.resolved_at.isoformat()
            }
        )
        db.session.add(event)
        
        db.session.commit()
