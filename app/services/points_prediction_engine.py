from typing import Optional
from datetime import datetime
from app import db
from app.services.points_ledger import PointsLedger
from app.services.points_service import PointsService
from app.services.xp_service import XPService
from app.services.amm_service import AMMService
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
        and platform fee accumulation in PlatformWallet. Uses AMM to determine share allocation and odds.

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
            ValueError: If no liquidity pool exists for the market
            ValueError: If stake exceeds max liquidity
        """
        from app.models import User, Market, Prediction, PlatformWallet, LiquidityPool
        
        # Check prediction deadline
        if market.status == 'resolved':
            raise ValueError(f"Market {market.id} is already resolved")
        if datetime.utcnow() > market.deadline:
            raise ValueError(f"Prediction deadline for market {market.id} has passed")

        # Get or create liquidity pool for market
        pool = LiquidityPool.query.filter_by(market_id=market.id).first()
        if not pool:
            raise ValueError(f"No liquidity pool found for market {market.id}")

        # Check max liquidity limit
        if (pool.yes_liquidity + pool.no_liquidity + shares) > Config.MAX_MARKET_LIQUIDITY:
            raise ValueError(f"Stake exceeds maximum market liquidity")

        # If using liquidity buffer, check balance
        if use_liquidity_buffer:
            if user.liquidity_buffer_deposit < shares:
                raise ValueError(f"Insufficient liquidity buffer balance. Required: {shares}, Available: {user.liquidity_buffer_deposit}")

        # Calculate platform fee (5%)
        platform_fee = 0.05 * shares
        net_shares = shares - platform_fee

        # Calculate share allocation using AMM
        amm_result = AMMService.calculate_share_allocation(
            market_id=market.id,
            outcome=outcome,
            amount=net_shares
        )
        
        # Update pool liquidity with new values from AMM
        pool.yes_liquidity = amm_result['yes_liquidity']
        pool.no_liquidity = amm_result['no_liquidity']
        
        # Update pool odds
        AMMService.update_odds(pool)

        # Add platform fee to wallet
        wallet = PlatformWallet.get_instance()
        wallet.add_fee(platform_fee)

        # Create prediction
        prediction = Prediction(
            user_id=user.id,
            market_id=market.id,
            outcome=outcome,
            confidence=amm_result['shares_purchased'],  # Use actual shares purchased as confidence
            stake=shares,
            timestamp=datetime.utcnow()
        )
        db.session.add(prediction)
        
        # Log prediction event
        MarketEvent.log_prediction(
            market=market,
            user_id=user.id,
            stake=shares,
            outcome=outcome
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
            is_correct = prediction.outcome is True if correct_outcome else prediction.outcome is False

            if is_correct:
                # Award points and XP
                PointsPredictionEngine.award_points_for_prediction(prediction)
                XPService.award_prediction_xp(prediction.user, success=True)
                prediction.xp_awarded = True

        # Resolve the market
        market.resolve('YES' if correct_outcome else 'NO')
        market.award_xp_for_predictions()
        db.session.commit()
