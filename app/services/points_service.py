<<<<<<< HEAD
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
=======
from flask import current_app
from app.models import User, db
from datetime import datetime

class PointsService:
    @staticmethod
    def deposit_to_lb(user_id, amount):
        """Deposit points to Liquidity Buffer"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
            
        if amount <= 0 or amount > user.points:
            return False
        
        user.points -= amount
        user.lb_deposit += amount
        db.session.commit()
        return True

    @staticmethod
    def withdraw_from_lb(user_id, amount):
        """Withdraw points from Liquidity Buffer"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
            
        if amount <= 0 or amount > user.lb_deposit:
            return False
        
        user.points += amount
        user.lb_deposit -= amount
        db.session.commit()
        return True

    @staticmethod
    def get_lb_yield(user_id):
        """Calculate daily yield from Liquidity Buffer"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
            
        total_lb = db.session.query(func.sum(User.lb_deposit)).scalar() or 0
        if total_lb == 0:
            return 0
            
        base_yield = current_app.config.get('LB_BASE_YIELD', 6)  # 6% annual yield
        active_markets = Market.query.filter_by(resolved=False).count()
        yield_adjustment = min(2, active_markets / 10)  # Up to 2% bonus for active markets
            
        daily_yield = (base_yield + yield_adjustment) / 365
        return (user.lb_deposit * daily_yield) / 100

    @staticmethod
    def update_reliability(user_id, was_correct):
        """Update reliability index based on prediction accuracy"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
            
        if was_correct:
            user.reliability_index = min(100.0, user.reliability_index + (20 / (1 + len(user.predictions))))
            user.xp += 10
        else:
            user.reliability_index = max(0.0, user.reliability_index - (10 / (1 + len(user.predictions))))
        db.session.commit()

    @staticmethod
    def get_total_points(user_id):
        """Get total points for a user including LB deposit"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
            
        return user.points + user.lb_deposit
>>>>>>> d745d5f (Fix badge image rendering and static path config)
