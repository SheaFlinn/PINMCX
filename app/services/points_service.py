from datetime import datetime, timedelta
from app.models import User
from app.extensions import db

class PointsService:
    @staticmethod
    def award_xp(user: User, xp_amount: int) -> None:
        """Award XP to a user with streak bonus multiplier
        
        Args:
            user: The User object to award XP to
            xp_amount: Base amount of XP to award
        """
        # Get today's UTC date
        today = datetime.utcnow().date()
        
        # Check if already checked in today
        if user.last_check_in_date and user.last_check_in_date.date() == today:
            return
        
        # Initialize streak if first check-in
        if not user.last_check_in_date:
            user.current_streak = 1
            user.last_check_in_date = datetime.combine(today, datetime.min.time())
        else:
            # Check if streak continues
            if user.last_check_in_date.date() == (today - timedelta(days=1)):
                user.current_streak += 1
            else:
                # Missed day, reset streak
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
