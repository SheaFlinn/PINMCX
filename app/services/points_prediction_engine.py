from typing import Optional
from datetime import datetime
from app import db
from app.services.points_ledger import PointsLedger
from app.services.points_service import PointsService
from app.models.market_event import MarketEvent
from config import Config

# Import models locally where needed
class PointsPredictionEngine:
    """
    Central service for handling predictions, their evaluation, and XP awards.
    Provides safety checks and ledger logging for all prediction-related operations.
    """

    @staticmethod
    def place_prediction(user: 'User', market: 'Market', shares: float, outcome: bool, use_liquidity_buffer: bool = False) -> 'Prediction':
        """
        Place a prediction on a market with platform fee deduction, optional liquidity buffer staking,
        and platform fee accumulation in PlatformWallet.

        Supports multiple predictions per user on the same market (re-betting). Each prediction is
        treated as a distinct unit of stake, allowing users to adjust their position over time.

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
            ValueError: If using liquidity buffer and insufficient balance
        """
        from app.models import User, Market, Prediction, PlatformWallet
        # Check prediction deadline
        if market.status == 'resolved':
            raise ValueError(f"Market {market.id} is already resolved")
        if datetime.utcnow() > market.deadline:
            raise ValueError(f"Prediction deadline for market {market.id} has passed")

        # If using liquidity buffer, check balance
        if use_liquidity_buffer:
            if user.liquidity_buffer_deposit < shares:
                raise ValueError(f"Insufficient liquidity buffer balance. Required: {shares}, Available: {user.liquidity_buffer_deposit}")

        # Calculate platform fee (5%)
        platform_fee = 0.05 * shares
        net_shares = shares - platform_fee

        # Add platform fee to wallet
        wallet = PlatformWallet.get_instance()
        wallet.add_fee(platform_fee)

        # Create prediction
        prediction = Prediction(
            user_id=user.id,
            market_id=market.id,
            outcome='YES' if outcome else 'NO',
            confidence=net_shares,
            stake=shares,
            timestamp=datetime.utcnow()
        )
        db.session.add(prediction)
        
        # Log prediction event
        MarketEvent.log_prediction(
            market=market,
            user_id=user.id,
            stake=shares,
            outcome='YES' if outcome else 'NO'
        )
        
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

        db.session.commit()

        return prediction

    @staticmethod
    def evaluate_prediction(prediction: 'Prediction', market: 'Market') -> bool:
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
        from app.models import Prediction, Market
        if market.status != 'resolved':
            raise ValueError(f"Market {market.id} is not resolved")

        # Prediction is correct if:
        # - Market resolved YES and prediction was YES
        # - Market resolved NO and prediction was NO
        return market.outcome == prediction.outcome

    @staticmethod
    def award_points_for_prediction(prediction: 'Prediction') -> None:
        """
        Award points for a correct prediction based on gross shares.
        
        Args:
            prediction: Prediction to award points for
        """
        from app.models import Prediction
        if prediction.points_awarded:
            return

        # Calculate points based on gross shares (no fee deduction)
        points_awarded = int(prediction.stake)
        
        # Update user points
        prediction.user.points += points_awarded
        
        # Log points award
        PointsLedger.log_transaction(
            user_id=prediction.user_id,
            amount=points_awarded,
            transaction_type="points_awarded",
            description=f"Points awarded for correct prediction on market {prediction.market_id}"
        )

        # Mark points as awarded
        prediction.points_awarded = True
        db.session.commit()

    @staticmethod
    def award_xp_for_prediction(prediction: 'Prediction') -> None:
        """
        Award XP for a prediction based on its outcome and stake.
        
        Args:
            prediction: The Prediction object to award XP for
        """
        user = prediction.user
        market = prediction.market
        
        # Only award XP if prediction hasn't been awarded XP before
        if prediction.xp_awarded:
            return
            
        # Only award XP for correct predictions
        if not prediction.is_correct():
            prediction.xp_awarded = True
            db.session.commit()
            return
            
        # Calculate XP based on stake
        base_xp = 100  # Base XP amount
        xp_award = int(base_xp * prediction.stake)
        
        # Award XP
        prediction.user.xp += xp_award
        prediction.xp_awarded = True

        # Log transaction
        PointsLedger.log_transaction(
            user_id=prediction.user_id,
            amount=xp_award,
            transaction_type='xp_awarded',
            description=f'XP awarded for correct prediction on market {prediction.market_id}'
        )
        
        # Log event with prediction details
        MarketEvent.log_prediction(
            market=market,
            user_id=user.id,
            stake=prediction.stake,
            outcome=prediction.outcome
        )
        
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
        from app.models import Market, Prediction
        # Get market
        market = Market.query.get(market_id)
        if not market:
            raise ValueError(f"Market {market_id} not found")

        # Check if market is already resolved
        if market.status == 'resolved':
            raise ValueError(f"Market {market_id} is already resolved")

        # Get all predictions for this market
        predictions = Prediction.query.filter_by(market_id=market_id).all()

        # Process each prediction
        for prediction in predictions:
            # Skip if points already awarded
            if prediction.points_awarded:
                continue

            # Check if prediction was correct
            is_correct = prediction.outcome == ('YES' if correct_outcome else 'NO')

            if is_correct:
                # Award points and XP
                PointsPredictionEngine.award_points_for_prediction(prediction)
                PointsPredictionEngine.award_xp_for_prediction(prediction)

        # Resolve the market
        market.resolve('YES' if correct_outcome else 'NO')
        db.session.commit()
