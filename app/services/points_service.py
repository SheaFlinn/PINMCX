from datetime import datetime, timedelta
from app.extensions import db
from app.models import User

class PointsService:
    @staticmethod
    def award_xp(user: User, xp_amount: int) -> None:
        """
        Award XP to a user with streak bonus multiplier.
        Applies daily check-in logic and boosts for streaks.
        """
        today = datetime.utcnow().date()

        # Skip if XP already awarded today
        if user.last_check_in_date and user.last_check_in_date.date() == today:
            return

        # Determine streak
        if user.last_check_in_date:
            delta = (today - user.last_check_in_date.date()).days
            if delta == 1:
                user.current_streak += 1
            else:
                user.current_streak = 1
        else:
            user.current_streak = 1

        user.last_check_in_date = datetime.utcnow()
        user.longest_streak = max(user.longest_streak, user.current_streak)

        # Streak multiplier (max 2x)
        bonus_multiplier = min(1.0 + 0.1 * (user.current_streak - 1), 2.0)
        final_xp = int(xp_amount * bonus_multiplier)

        user.xp += final_xp
        db.session.commit()

    @staticmethod
    def get_user_xp(user: User) -> int:
        return user.xp

    @staticmethod
    def get_user_streak(user: User) -> int:
        return user.current_streak

    @staticmethod
    def get_total_points(user_id: int) -> int:
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        return user.points + user.lb_deposit
