from typing import Union
from .models import User, Market, Prediction, LiquidityProvider, Badge
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db

class PointsError(Exception):
    pass

class InsufficientPointsError(PointsError):
    pass

class InvalidOperationError(PointsError):
    pass

class PointsService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def award_badge_if_not_exists(self, user: User, badge_type: str):
        badge = Badge.query.filter_by(type=badge_type).first()
        if badge and badge not in user.badges:
            user.badges.append(badge)
            db.session.commit()

    def validate_points(self, user: User, amount: int):
        if amount <= 0:
            raise InvalidOperationError("Amount must be positive")
        if user.points < amount:
            raise InsufficientPointsError(f"Insufficient points. Available: {user.points}, Required: {amount}")

    def validate_lb_points(self, user: User, amount: int):
        if amount <= 0:
            raise InvalidOperationError("Amount must be positive")
        if user.lb_deposit < amount:
            raise InsufficientPointsError(f"Insufficient LB points. Available: {user.lb_deposit}, Required: {amount}")

    def transfer_points(self, user: User, amount: int, source: str = "wallet"):
        if source == "wallet":
            self.validate_points(user, amount)
            user.points -= amount
        elif source == "lb":
            self.validate_lb_points(user, amount)
            user.lb_deposit -= amount
        else:
            raise InvalidOperationError(f"Invalid source: {source}")

    def return_points(self, user: User, amount: int, source: str = "wallet"):
        if source == "wallet":
            user.points += amount
        elif source == "lb":
            user.lb_deposit += amount
        else:
            raise InvalidOperationError(f"Invalid source: {source}")

    def calculate_prediction_price(self, market: Market, outcome: str, amount: int) -> float:
        if outcome not in ['YES', 'NO']:
            raise InvalidOperationError("Outcome must be 'YES' or 'NO'")
        total_pool = market.yes_pool + market.no_pool
        return (market.no_pool if outcome == 'YES' else market.yes_pool) / total_pool * amount

    def calculate_prediction_payout(self, market: Market, prediction: Prediction) -> float:
        if not market.resolved:
            raise InvalidOperationError("Market is not resolved")
        total_pool = market.yes_pool + market.no_pool
        pool = market.yes_pool if prediction.outcome == 'YES' else market.no_pool
        return prediction.amount * (total_pool / pool) if market.resolved_outcome == prediction.outcome else 0

    def calculate_lb_yield(self, user: User) -> float:
        total_lb = self.db.query(func.sum(User.lb_deposit)).scalar() or 0
        if total_lb == 0:
            return 0
        base_yield = 6  # %
        active_markets = Market.query.filter_by(resolved=False).count()
        yield_adjustment = min(2, active_markets / 10)
        daily_yield = (base_yield + yield_adjustment) / 365
        return (user.lb_deposit * daily_yield) / 100

    def update_reliability(self, user: User, was_correct: bool):
        base_change = 20 if was_correct else 10
        adjustment = base_change / (1 + len(user.predictions))
        if was_correct:
            user.reliability_index = min(100.0, user.reliability_index + adjustment)
            user.xp += 10
            if user.xp >= 100:
                self.award_badge_if_not_exists(user, 'xp_100')
            if user.xp >= 500:
                self.award_badge_if_not_exists(user, 'xp_500')
            if user.xp >= 1000:
                self.award_badge_if_not_exists(user, 'xp_1000')
        else:
            user.reliability_index = max(0.0, user.reliability_index - adjustment)
        db.session.commit()

    def award_xp(self, user: User, xp_amount: int):
        today = datetime.combine(datetime.utcnow().date(), datetime.min.time())
        if user.last_check_in_date and user.last_check_in_date.date() == today.date():
            return
        if user.last_check_in_date and user.last_check_in_date.date() == (today - timedelta(days=1)).date():
            user.current_streak += 1
        else:
            user.current_streak = 1
        user.last_check_in_date = today
        user.longest_streak = max(user.longest_streak, user.current_streak)
        multiplier = min(1.0 + 0.1 * user.current_streak, 2.0)
        user.xp += int(xp_amount * multiplier)
        db.session.commit()

    @staticmethod
    def update_streak(user: User):
        today = datetime.utcnow().date()
        if not user.last_check_in_date:
            user.last_check_in_date = today
            user.current_streak = 1
            user.longest_streak = 1
        else:
            last_date = user.last_check_in_date.date() if isinstance(user.last_check_in_date, datetime) else user.last_check_in_date
            days_since_last = (today - last_date).days
            if days_since_last == 1:
                user.current_streak += 1
            elif days_since_last > 1:
                user.current_streak = 1
            user.last_check_in_date = today
        if user.current_streak >= 5:
            PointsService.award_badge_if_not_exists(user, 'daily_streak_5')
        if user.current_streak >= 10:
            PointsService.award_badge_if_not_exists(user, 'daily_streak_10')
        if user.current_streak >= 30:
            PointsService.award_badge_if_not_exists(user, 'daily_streak_30')
        db.session.commit()
