from datetime import datetime, timedelta
from app.extensions import db
from app.models import User, LiquidityPool, Market, Prediction

class PointsService:
    @staticmethod
    def award_xp(user: User, xp_amount: int) -> None:
        """
        Award XP to a user with streak bonus multiplier.
        Applies increasing bonus for daily check-ins.
        """
        # Check if XP already awarded today
        if user.last_check_in_date and user.last_check_in_date.date() == datetime.utcnow().date():
            return

        today = datetime.utcnow().date()
        if user.last_check_in_date:
            days_since_last = (today - user.last_check_in_date.date()).days
            if days_since_last == 1:
                user.current_streak += 1
            else:
                user.current_streak = 1
        else:
            user.current_streak = 1

        user.longest_streak = max(user.longest_streak, user.current_streak)

        # Streak bonus: max 2x at 30 days
        bonus = min(1.0 + 0.1 * (user.current_streak - 1), 2.0)
        final_xp = int(xp_amount * bonus)

        user.xp += final_xp
        user.last_check_in_date = datetime.utcnow()

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

class LiquidityPoolService:
    @staticmethod
    def fund_pool(user: User, contract_id: int, amount: int) -> None:
        """Fund a liquidity pool using user's LB"""
        if user.lb_deposit < amount:
            raise ValueError("Insufficient LB balance")

        pool = LiquidityPool.query.filter_by(contract_id=contract_id).first()
        if not pool:
            raise ValueError("Liquidity pool not found")

        if pool.current_liquidity + amount > pool.max_liquidity:
            raise ValueError("Funding exceeds pool cap")

        user.lb_deposit -= amount
        pool.current_liquidity += amount

        db.session.commit()

def award_xp_for_resolved_market(market_id: int) -> None:
    """Award XP to users who predicted the correct outcome"""
    market = Market.query.get(market_id)
    if not market or not market.resolved or not market.resolved_outcome:
        return

    correct_predictions = Prediction.query.filter_by(
        market_id=market_id,
        outcome=market.resolved_outcome
    ).all()

    for prediction in correct_predictions:
        user = User.query.get(prediction.user_id)
        if user:
            user.xp = (user.xp or 0) + 10

    db.session.commit()
