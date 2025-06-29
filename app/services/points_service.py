from datetime import datetime, timedelta
from app.extensions import db
from app.models import User, LiquidityPool

class PointsService:
    @staticmethod
    def award_xp(user, xp_amount: int) -> None:
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
           
        2. Streak System:
           - Streak starts at 1 on first check-in
           - Increases by 1 each consecutive day
           - Resets to 1 if a day is missed
           - Longest streak is tracked separately
           
        3. Multiplier System:
           - Base multiplier is 1.0
           - Adds 0.1 per consecutive day
           - Caps at 2.0 (max 10 consecutive days)
        """
        # Get today's date in UTC
        today = datetime.utcnow().date()
        
        # Check if user has checked in today
        if user.last_check_in_date:
            if isinstance(user.last_check_in_date, datetime):
                last_date = user.last_check_in_date.date()
            else:
                last_date = user.last_check_in_date
            
            if last_date == today:
                return  # Already checked in today
            
        # Update streak
        if user.last_check_in_date:
            if isinstance(user.last_check_in_date, datetime):
                last_date = user.last_check_in_date.date()
            else:
                last_date = user.last_check_in_date
            days_since_last = (today - last_date).days
            
            if days_since_last == 1:
                user.current_streak += 1
            else:
                # Missed day, reset streak
                user.current_streak = 1
                user.last_check_in_date = datetime.combine(today, datetime.min.time())
        else:
            user.current_streak = 1
            user.last_check_in_date = datetime.combine(today, datetime.min.time())
        
        # Update longest streak if needed
        if user.current_streak > user.longest_streak:
            user.longest_streak = user.current_streak
        
        # Calculate streak bonus multiplier (max 2.0)
        multiplier = min(2.0, 1.0 + 0.1 * (user.current_streak - 1))
        
        # Update XP
        user.xp += int(xp_amount * multiplier)
        
        # Commit changes
        db.session.commit()

class LiquidityPoolService:

    @staticmethod
    def fund_pool(user: User, contract_id: int, amount: int) -> bool:
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
        return True
