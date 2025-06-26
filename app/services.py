from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.extensions import db
from app.models import User, Market, Prediction, LiquidityProvider, Badge

class PointsError(Exception):
    pass

class InsufficientPointsError(PointsError):
    pass

class InvalidOperationError(PointsError):
    pass

class PointsService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def validate_points(self, user: User, amount: int):
        if amount <= 0:
            raise InvalidOperationError("Amount must be positive")
        if user.points < amount:
            raise InsufficientPointsError(
                f"Insufficient points. Available: {user.points}, Required: {amount}"
            )

    def validate_lb_points(self, user: User, amount: int):
        if amount <= 0:
            raise InvalidOperationError("Amount must be positive")
        if user.lb_deposit < amount:
            raise InsufficientPointsError(
                f"Insufficient LB points. Available: {user.lb_deposit}, Required: {amount}"
            )

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
        if outcome == 'YES':
            return market.no_pool / total_pool * amount
        else:
            return market.yes_pool / total_pool * amount

    def calculate_prediction_payout(self, market: Market, prediction: Prediction) -> float:
        if not market.resolved:
            raise InvalidOperationError("Market is not resolved")
        total_pool = market.yes_pool + market.no_pool
        if market.resolved_outcome == prediction.outcome:
            if prediction.outcome == 'YES':
                return prediction.amount * (total_pool / market.yes_pool)
            else:
                return prediction.amount * (total_pool / market.no_pool)
        return 0

    def calculate_lb_yield(self, user: User) -> float:
        total_lb = self.db.query(func.sum(User.lb_deposit)).scalar() or 0
        if total_lb == 0:
            return 0
        base_yield = 6
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
        if user.current_streak > user.longest_streak:
            user.longest_streak = user.current_streak
        multiplier = min(1.0 + 0.1 * user.current_streak, 2.0)
        final_award = int(xp_amount * multiplier)
        user.xp += final_award
        db.session.commit()

    def get_liquidity_provider_shares(self, user: User, market: Market) -> float:
        lp = LiquidityProvider.query.filter_by(user_id=user.id, market_id=market.id).first()
        return lp.shares if lp else 0.0
