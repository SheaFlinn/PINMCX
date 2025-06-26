

from datetime import datetime, timedelta
from app.extensions import db

# Import models locally where needed
class PointsService:
    @staticmethod
    def award_xp(user: 'User', xp_amount: int) -> None:
        """
        Award XP to a user with streak bonus multiplier.
        
        Args:
            user: The User object to award XP to
            xp_amount: Base amount of XP to award
            
        XP Awarding Rules:
        1. Daily Check-in:
           - XP can only be awarded once per day
           - Checked against user.last_check_in_date
           - Reset at midnight UTC
           
        2. Streak Bonus:
           - No bonus on first day
           - 10% bonus for 2+ consecutive days
           - 20% bonus for 14+ consecutive days
           - 30% bonus for 21+ consecutive days
           - 40% bonus for 30+ consecutive days
        """
        from app.models import User
        
        # Check if XP can be awarded today
        if user.last_check_in_date and user.last_check_in_date.date() == datetime.utcnow().date():
            return
            
        # Calculate streak bonus
        today = datetime.utcnow().date()
        if user.last_check_in_date:
            days_since_last = (today - user.last_check_in_date.date()).days
            if days_since_last == 1:
                user.current_streak += 1
            else:
                user.current_streak = 1
                
            # Update longest streak if needed
            if user.current_streak > user.longest_streak:
                user.longest_streak = user.current_streak
        else:
            user.current_streak = 1
            user.longest_streak = 1
            
        # Apply streak bonus (only after first day)
        bonus = 1.0  # Start with no bonus
        if user.current_streak >= 2:
            bonus = min(1.0 + 0.1 * (user.current_streak - 1), 2.0)  # Calculate bonus (10% per day after first day, max 2.0x)
            
        # Award XP with bonus
        xp_to_award = int(xp_amount * bonus)
        user.xp += xp_to_award
        
        # Update last check-in date
        user.last_check_in_date = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def get_user_xp(user: 'User') -> int:
        """Get user's current XP balance"""
        from app.models import User
        return user.xp

    @staticmethod
    def get_user_streak(user: 'User') -> int:
        """Get user's current streak"""
        from app.models import User
        return user.current_streak

class LiquidityPoolService:
    @staticmethod
    def fund_pool(user: 'User', contract_id: int, amount: int) -> None:
        """
        Fund a liquidity pool with points from a user's balance.
        
        Args:
            user: User object funding the pool
            contract_id: ID of the contract associated with the pool
            amount: Amount of points to fund
            
        Raises:
            ValueError: If user has insufficient points
        """
        from app.models import User, LiquidityPool
        
        if user.lb_balance < amount:
            raise ValueError("Insufficient LB balance")

        pool = LiquidityPool.query.filter_by(contract_id=contract_id).first()
        if not pool:
            raise ValueError("Liquidity pool not found")

        if pool.current_liquidity + amount > pool.max_liquidity:
            raise ValueError("Funding exceeds pool cap")

        # Deduct from LB and update pool
        user.lb_balance -= amount
        pool.current_liquidity += amount

        db.session.commit()

def award_xp_for_resolved_market(market_id):
    # Get the market
    market = Market.query.get(market_id)
    if not market or not market.resolved or not market.correct_outcome:
        return

    # Get all correct predictions
    correct_predictions = Prediction.query.filter_by(
        market_id=market_id,
        prediction=market.correct_outcome
    ).all()

    # Award XP to each correct user
    for prediction in correct_predictions:
        user = User.query.get(prediction.user_id)
        if user:
            user.xp = (user.xp or 0) + 10

    db.session.commit()

def get_total_points(user_id):
    """Get total points for a user including LB deposit"""
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")
            
    return user.points + user.lb_deposit
