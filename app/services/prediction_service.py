from datetime import datetime
from typing import Optional

from app.models import User, Market, Prediction, MarketEvent
from app.services.amm_service import AMMService
from app.services.xp_service import XPService
from app import db

class PredictionService:
    """
    Service for managing predictions and their lifecycle.
    Handles point/liquidity buffer deductions, AMM integration,
    and prediction resolution with XP awards.
    """
    
    @staticmethod
    def place_prediction(
        user: User,
        market: Market,
        stake: float,
        outcome: bool,
        use_liquidity_buffer: bool = False
    ) -> Prediction:
        """
        Place a prediction on a market.
        
        Args:
            user: User placing the prediction
            market: Market to predict on
            stake: Amount of points to stake
            outcome: True for 'YES', False for 'NO'
            use_liquidity_buffer: Whether to use liquidity buffer instead of points
            
        Returns:
            Prediction object
            
        Raises:
            ValueError: If stake is not positive
            ValueError: If outcome is not a boolean
            ValueError: If user doesn't have sufficient points or buffer
        """
        # Ensure user and market are committed
        if not user.id or not market.id:
            raise ValueError("User and Market must be committed to the database first")
            
        # Ensure we have fresh state from the database
        user = db.session.get(User, user.id)
        market = db.session.get(Market, market.id)
        
        if stake <= 0:
            raise ValueError("Stake must be positive")
            
        if not isinstance(outcome, bool):
            raise ValueError("Outcome must be a boolean value (True or False)")
            
        # Deduct points or liquidity buffer
        if use_liquidity_buffer:
            if user.lb_deposit < stake:
                raise ValueError("Insufficient liquidity buffer balance")
            user.lb_deposit -= stake
        else:
            if user.points < stake:
                raise ValueError("Insufficient points")
            user.points -= stake
            
        # Calculate new pool state
        result = AMMService.calculate_share_allocation(
            stake,
            outcome,
            market.id
        )
        
        # Update pool liquidity
        market.yes_pool = result['yes_liquidity']
        market.no_pool = result['no_liquidity']
        
        # Create prediction
        prediction = Prediction(
            user_id=user.id,
            market_id=market.id,
            stake=stake,
            outcome=outcome,
            shares=result['shares'],
            shares_purchased=result['shares'],
            price=result['price'],
            used_liquidity_buffer=use_liquidity_buffer,
            awarded_xp=0
        )
        
        # Add to session and commit
        db.session.add_all([user, market, prediction])
        db.session.commit()
        
        # Refresh prediction after commit
        prediction = db.session.get(Prediction, prediction.id)
        
        return prediction

    @staticmethod
    def resolve_prediction(prediction: Prediction, market: Market) -> None:
        """
        Resolve a prediction based on market outcome.
        
        Args:
            prediction: Prediction to resolve
            market: Market that was predicted on
            
        Raises:
            ValueError: If market is not resolved
            ValueError: If prediction is already resolved
        """
        # Ensure prediction and market are committed
        if not prediction.id or not market.id:
            raise ValueError("Prediction and Market must be committed to the database first")
        
        # Ensure we have fresh state from the database
        prediction = db.session.get(Prediction, prediction.id)
        market = db.session.get(Market, market.id)
        
        if not market.resolved_at:
            raise ValueError("Market must be resolved before resolving predictions")
        
        if prediction.resolved_at:
            raise ValueError("Prediction is already resolved")
        
        # Calculate outcome
        outcome = market.resolved_outcome == "YES"
        
        # Award points if prediction matches market outcome
        if (outcome is True and prediction.outcome is True) or \
           (outcome is False and prediction.outcome is False):
            points = prediction.shares * market.liquidity_pool
            user = db.session.get(User, prediction.user_id)
            user.points += points
            prediction.awarded_points = points
        
        # Award XP only if prediction matches market outcome
        if (outcome is True and prediction.outcome is True) or (outcome is False and prediction.outcome is False):
            xp_awarded = XPService.award_prediction_xp(prediction.user, success=True)
            prediction.awarded_xp = int(xp_awarded) if xp_awarded is not None else 0
        else:
            prediction.awarded_xp = 0
    
        # Mark prediction as resolved
        prediction.resolved_at = datetime.utcnow()
        db.session.commit()
