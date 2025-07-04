from app.extensions import db
from app.models import User
from datetime import datetime, timedelta

class XPService:
    """
    Handles XP accrual, streaks, and engagement logic.
    Supports check-in streaks, prediction rewards, and civic access gating.
    """

    @staticmethod
    def award_prediction_xp(user: User, success: bool = True):
        base_xp = 10
        bonus = 5 if success else 0
        xp_awarded = base_xp + bonus
        user.xp += xp_awarded
        user.increment_predictions()
        if success:
            user.increment_successful_predictions()
        XPService._update_reliability(user)
        db.session.commit()
        return xp_awarded

    @staticmethod
    def check_in(user: User):
        today = datetime.utcnow().date()
        last = user.last_check_in_date.date() if user.last_check_in_date else None

        if last == today:
            return  # already checked in today

        if last == today - timedelta(days=1):
            user.current_streak += 1
        else:
            user.current_streak = 1

        user.longest_streak = max(user.longest_streak, user.current_streak)
        user.last_check_in_date = datetime.utcnow()
        
        # Award XP for check-in
        base_xp = 5
        streak_bonus = 2 * user.current_streak
        user.xp += base_xp + streak_bonus
        
        db.session.commit()

    @staticmethod
    def _update_reliability(user: User):
        if user.predictions_count == 0:
            user.reliability_index = 50.0
            return

        success_rate = user.successful_predictions / user.predictions_count
        user.reliability_index = min(100.0, max(0.0, success_rate * 100.0))
