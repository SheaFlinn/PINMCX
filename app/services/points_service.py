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
