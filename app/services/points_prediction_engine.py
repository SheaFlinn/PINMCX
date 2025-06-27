from typing import Optional
from datetime import datetime
from app.models import User, Market, Prediction, db, MarketEvent
from app.services.points_ledger import PointsLedger
from config import Config

class PointsPredictionEngine:
    """
    Central service for handling predictions, their evaluation, and XP awards.
    Provides safety checks and ledger logging for all prediction-related operations.
    """

    @staticmethod
    def place_prediction(user: User, market: Market, shares: float, outcome: bool, use_liquidity_buffer: bool = False) -> Prediction:
        """
        Place a prediction on a market with platform fee deduction and optional liquidity buffer staking.

        Args:
            user: User placing the prediction
            market: Market to predict on
            shares: Number of shares to purchase
            outcome: Predicted outcome (True for YES, False for NO)
            use_liquidity_buffer: If True, use liquidity buffer instead of normal points

        Returns:
            Prediction object

        Raises:
            ValueError: If prediction is placed after market deadline
            ValueError: If user already has prediction on this market
            ValueError: If using liquidity buffer and insufficient balance
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

        # If using liquidity buffer, check balance
        if use_liquidity_buffer:
            if user.liquidity_buffer_deposit < shares:
                raise ValueError(f"Insufficient liquidity buffer balance. Required: {shares}, Available: {user.liquidity_buffer_deposit}")

        # Calculate platform fee (5%)
        platform_fee = 0.05 * shares
        net_shares = shares - platform_fee

        # Create prediction
        prediction = Prediction(
            user=user,
            market=market,
            shares=shares,  # Store original shares amount
            platform_fee=platform_fee,
            outcome=outcome,
            used_liquidity_buffer=use_liquidity_buffer,
            created_at=datetime.utcnow()
        )
        db.session.add(prediction)
        db.session.commit()

        # If using liquidity buffer, deduct from deposit
        if use_liquidity_buffer:
            user.liquidity_buffer_deposit -= shares
            PointsLedger.log_transaction(
                user=user,
                amount=-shares,
                transaction_type="liquidity_buffer_stake",
                description=f"Stake placed from liquidity buffer for market {market.id}"
            )
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
        Award XP to users with correct predictions based on gross shares.

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
                # Calculate XP based on gross shares (no fee deduction)
                xp_awarded = int(prediction.shares)
                
                # Update user XP
                prediction.user.xp += xp_awarded
                
                # Log XP award in ledger
                PointsLedger.log_transaction(
                    user=prediction.user,
                    amount=0,
                    transaction_type="xp_awarded",
                    description=f"XP awarded for correct prediction on market {market.id}"
                )

                # Mark XP as awarded
                prediction.xp_awarded = True

        db.session.commit()

    @staticmethod
    def resolve_market(market_id: int, correct_outcome: bool) -> None:
        """
        Resolve a market and award points/XP for correct predictions.
        XP is awarded on gross shares, points on net shares (shares - platform_fee).

        Args:
            market_id: ID of the market to resolve
            correct_outcome: The correct outcome (True for YES, False for NO)

        Raises:
            ValueError: If market is already resolved
        """
        # Get market
        market = Market.query.get(market_id)
        if not market:
            raise ValueError(f"Market {market_id} not found")

        # Check if market is already resolved
        if market.resolved:
            raise ValueError(f"Market {market_id} is already resolved")

        # Get all predictions for this market
        predictions = Prediction.query.filter_by(market_id=market_id).all()

        # Process each prediction
        for prediction in predictions:
            # Skip if points already awarded
            if prediction.xp_awarded:
                continue

            # Check if prediction was correct
            is_correct = prediction.outcome == correct_outcome

            if is_correct:
                # Calculate points based on net shares (shares - platform_fee)
                points_awarded = int(prediction.shares - (prediction.platform_fee or 0.0))
                
                # Update user points
                prediction.user.points += points_awarded
                
                # Log points award
                PointsLedger.log_transaction(
                    user=prediction.user,
                    amount=points_awarded,
                    transaction_type="points_awarded",
                    description=f"Points awarded for correct prediction on market {market_id}"
                )

                # Award XP based on gross shares (no fee deduction)
                xp_awarded = int(prediction.shares)
                prediction.user.xp += xp_awarded

                # Log XP award
                PointsLedger.log_transaction(
                    user=prediction.user,
                    amount=0,
                    transaction_type="xp_awarded",
                    description=f"XP awarded for correct prediction on market {market_id}"
                )

                # Mark XP as awarded (also prevents double points)
                prediction.xp_awarded = True

        # Update market status
        market.resolved = True
        market.resolved_outcome = "YES" if correct_outcome else "NO"
        market.resolved_at = datetime.utcnow()

        # Log market resolution event
        MarketEvent.log_market_resolution(market, correct_outcome)

        # Commit all changes
        db.session.commit()
