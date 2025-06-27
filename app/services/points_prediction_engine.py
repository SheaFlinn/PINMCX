from typing import Optional
from datetime import datetime
from app.models import User, Market, Prediction, db
from app.services.points_ledger import PointsLedger
from config import Config

class PointsPredictionEngine:
    """
    Central service for handling predictions, their evaluation, and XP awards.
    Provides safety checks and ledger logging for all prediction-related operations.
    """

    @staticmethod
    def place_prediction(user: User, market: Market, shares: float, outcome: bool) -> Prediction:
        """
        Place a prediction on a market.

        Args:
            user: User placing the prediction
            market: Market to predict on
            shares: Number of shares to purchase
            outcome: Predicted outcome (True for YES, False for NO)

        Returns:
            Prediction object

        Raises:
            ValueError: If prediction is placed after market deadline
            ValueError: If user already has prediction on this market
        """
        # Check prediction deadline
        if market.resolved:
            raise ValueError(f"Market {market.id} is already resolved")
        if datetime.utcnow() > market.prediction_deadline:
            raise ValueError(f"Prediction deadline for market {market.id} has passed")

        # Check for existing prediction
        existing = Prediction.query.filter_by(
            user_id=user.id,
            market_id=market.id
        ).first()
        if existing:
            raise ValueError(f"User {user.id} already has prediction on market {market.id}")

        # Create prediction
        prediction = Prediction(
            user=user,
            market=market,
            shares=shares,
            outcome=outcome,
            created_at=datetime.utcnow()
        )
        db.session.add(prediction)
        db.session.commit()

        return prediction

    @staticmethod
    def evaluate_prediction(prediction: Prediction, market: Market) -> bool:
        """
        Evaluate if a prediction was correct.

        Args:
            prediction: Prediction to evaluate
            market: Resolved market

        Returns:
            bool: True if prediction was correct, False otherwise

        Raises:
            ValueError: If market is not resolved
        """
        if not market.resolved:
            raise ValueError(f"Market {market.id} is not resolved")

        # Prediction is correct if:
        # - Market resolved YES and prediction was YES
        # - Market resolved NO and prediction was NO
        return market.resolved_outcome == ("YES" if prediction.outcome else "NO")

    @staticmethod
    def award_xp_for_predictions(market: Market) -> None:
        """
        Award XP to users with correct predictions.

        Args:
            market: Resolved market to evaluate predictions for

        Raises:
            ValueError: If market is not resolved
        """
        if not market.resolved:
            raise ValueError(f"Market {market.id} is not resolved")

        # Get all predictions for this market
        predictions = Prediction.query.filter_by(market_id=market.id).all()

        for prediction in predictions:
            # Skip if XP already awarded
            if prediction.xp_awarded:
                continue

            # Check if prediction was correct
            is_correct = PointsPredictionEngine.evaluate_prediction(prediction, market)

            if is_correct:
                # Calculate XP based on shares (e.g., 1 XP per share)
                xp_awarded = int(prediction.shares)
                
                # Update user XP
                prediction.user.xp += xp_awarded
                
                # Log XP award in ledger
                PointsLedger.log_transaction(
                    user_id=prediction.user.id,
                    amount=0,
                    transaction_type="xp_awarded",
                    description=f"XP awarded for correct prediction on market {market.id}"
                )

                # Mark XP as awarded
                prediction.xp_awarded = True

        db.session.commit()
