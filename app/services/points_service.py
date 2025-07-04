from datetime import datetime, timedelta
from app.extensions import db
from app.models import User
from typing import Union, Optional

class PointsService:
    @staticmethod
    def _get_user(user_id_or_obj):
        """Helper method to get user from either ID or User object"""
        if isinstance(user_id_or_obj, User):
            return user_id_or_obj
        elif isinstance(user_id_or_obj, int):
            return User.query.get(user_id_or_obj)
        raise ValueError("Input must be a User object or user ID")

    @staticmethod
    def award_xp(user_id: int, amount: int) -> Optional[int]:
        """Add XP to user by ID"""
        from app.models import User
        from app.extensions import db

        user = User.query.get(user_id)
        if user:
            user.xp = (user.xp or 0) + amount
            db.session.commit()
            return user.xp
        return None

    @staticmethod
    def get_user_xp(user_id):
        """Get user's XP points by ID"""
        from app.models import User
        user = User.query.get(user_id)
        return user.xp if user else None

    @staticmethod
    def get_user_streak(user_id_or_obj: Union[User, int]) -> Optional[int]:
        """Get user's current streak"""
        user = PointsService._get_user(user_id_or_obj)
        return user.current_streak if user else None

    @staticmethod
    def get_user_streak(user_id: int) -> Optional[dict]:
        """Get user's streak information
        
        Returns:
            dict: {
                "current_streak": int,
                "longest_streak": int,
                "last_check_in": datetime
            }
            None: if user not found
        """
        from app.models import User
        user = User.query.get(user_id)
        if user:
            return {
                "current_streak": user.current_streak,
                "longest_streak": user.longest_streak,
                "last_check_in": user.last_check_in_date
            }
        return None

    @staticmethod
    def get_total_points(user_id_or_obj: Union[User, int]) -> Optional[int]:
        """Get user's total points (regular points + liquidity buffer)"""
        user = PointsService._get_user(user_id_or_obj)
        if not user:
            return None
        return user.points + user.lb_deposit
