from typing import Union
from .models import User, Market, Prediction, LiquidityProvider, Badge, user_badges
from sqlalchemy.orm import Session
<<<<<<< HEAD
from datetime import datetime, timedelta
=======
from datetime import datetime
>>>>>>> d745d5f (Fix badge image rendering and static path config)
from sqlalchemy import func
from app.extensions import db

class PointsError(Exception):
    """Base class for points-related errors"""
    pass

class InsufficientPointsError(PointsError):
    """Raised when a user doesn't have enough points for an operation"""
    pass

class InvalidOperationError(PointsError):
    """Raised when an operation is not allowed"""
    pass

class PointsService:
    """Service class for handling all points-related operations"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def award_badge_if_not_exists(self, user: User, badge_type: str):
        """Award a badge to a user if they haven't already received it"""
        badge = Badge.query.filter_by(type=badge_type).first()
        if not badge:
            return
        already_awarded = badge in user.badges
        if not already_awarded:
            user.badges.append(badge)
            db.session.commit()
    
    def validate_points(self, user: User, amount: int) -> None:
        """Validate that a user has sufficient points for an operation"""
        if amount <= 0:
            raise InvalidOperationError("Amount must be positive")
        if user.points < amount:
            raise InsufficientPointsError(
                f"Insufficient points. Available: {user.points}, Required: {amount}"
            )
    
    def validate_lb_points(self, user: User, amount: int) -> None:
        """Validate that a user has sufficient LB points for withdrawal"""
        if amount <= 0:
            raise InvalidOperationError("Amount must be positive")
        if user.lb_deposit < amount:
            raise InsufficientPointsError(
                f"Insufficient LB points. Available: {user.lb_deposit}, Required: {amount}"
            )
    
    def transfer_points(self, user: User, amount: int, source: str = "wallet") -> None:
        """Transfer points from user's wallet or LB to market prediction"""
        if source == "wallet":
            self.validate_points(user, amount)
            user.points -= amount
        elif source == "lb":
            self.validate_lb_points(user, amount)
            user.lb_deposit -= amount
        else:
            raise InvalidOperationError(f"Invalid source: {source}")
    
    def return_points(self, user: User, amount: int, source: str = "wallet") -> None:
        """Return points to user's wallet or LB"""
        if source == "wallet":
            user.points += amount
        elif source == "lb":
            user.lb_deposit += amount
        else:
            raise InvalidOperationError(f"Invalid source: {source}")
    
    def calculate_prediction_price(self, market: Market, outcome: str, amount: int) -> float:
        """Calculate price for placing a prediction"""
        if outcome not in ['YES', 'NO']:
            raise InvalidOperationError("Outcome must be 'YES' or 'NO'")
        
        total_pool = market.yes_pool + market.no_pool
        if outcome == 'YES':
            return market.no_pool / total_pool * amount
        else:
            return market.yes_pool / total_pool * amount
    
    def calculate_prediction_payout(self, market: Market, prediction: Prediction) -> float:
        """Calculate payout for a resolved prediction"""
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
        """Calculate daily yield from Liquidity Buffer"""
        total_lb = self.db.query(func.sum(User.lb_deposit)).scalar() or 0
        if total_lb == 0:
            return 0
            
        # Annual yield rate (4-8% as per the document)
        base_yield = 6  # 6% annual yield
        
        # Adjust yield based on market activity
        active_markets = Market.query.filter_by(resolved=False).count()
        yield_adjustment = min(2, active_markets / 10)  # Up to 2% bonus for active markets
        
        # Calculate daily yield
        daily_yield = (base_yield + yield_adjustment) / 365
        return (user.lb_deposit * daily_yield) / 100
    
    def update_reliability(self, user: User, was_correct: bool) -> None:
        """Update user's reliability index and grant XP"""
        base_change = 20 if was_correct else 10
        adjustment = base_change / (1 + len(user.predictions))
        
        if was_correct:
            user.reliability_index = min(100.0, user.reliability_index + adjustment)
            user.xp += 10
            
            # Award XP-based badges
            if user.xp >= 100:
                PointsService.award_badge_if_not_exists(user, 'xp_100')
            if user.xp >= 500:
                PointsService.award_badge_if_not_exists(user, 'xp_500')
            if user.xp >= 1000:
                PointsService.award_badge_if_not_exists(user, 'xp_1000')
        else:
            user.reliability_index = max(0.0, user.reliability_index - adjustment)

        db.session.commit()

<<<<<<< HEAD
    def award_xp(self, user: User, xp_amount: int) -> None:
        """Award XP to a user with streak bonus multiplier
        
        Args:
            user: The User object to award XP to
            xp_amount: Base amount of XP to award
        """
        # Get today's date at midnight
        today = datetime.combine(datetime.utcnow().date(), datetime.min.time())
        
        # Check last check-in date
        if user.last_check_in_date and user.last_check_in_date.date() == today.date():
            # Already checked in today, do nothing
            return
        
        # Calculate streak
        if user.last_check_in_date and user.last_check_in_date.date() == (today - timedelta(days=1)).date():
            # Check-in yesterday, increment streak
            user.current_streak += 1
        else:
            # Missed day or first check-in, reset streak
            user.current_streak = 1
        
        # Update last check-in date
        user.last_check_in_date = today
        
        # Update longest streak if needed
        if user.current_streak > user.longest_streak:
            user.longest_streak = user.current_streak
        
        # Calculate streak bonus multiplier
        multiplier = min(1.0 + 0.1 * user.current_streak, 2.0)
        final_award = int(xp_amount * multiplier)
        
        # Award XP
        user.xp += final_award
        
        # Commit changes
        db.session.commit()

=======
>>>>>>> d745d5f (Fix badge image rendering and static path config)
    @staticmethod
    def update_streak(user):
        today = datetime.utcnow().date()

        if not user.last_check_in_date:
            user.last_check_in_date = today
            user.current_streak = 1
            user.longest_streak = 1
        else:
            if isinstance(user.last_check_in_date, datetime):
                last_date = user.last_check_in_date.date()
            else:
                last_date = user.last_check_in_date
            days_since_last = (today - last_date).days

            if days_since_last == 1:
                user.current_streak += 1
            elif days_since_last is None or days_since_last > 1:
                user.current_streak = 1
            user.last_check_in_date = today

        # Award streak-based badges
        if user.current_streak >= 5:
            PointsService.award_badge_if_not_exists(user, 'daily_streak_5')
        if user.current_streak >= 10:
            PointsService.award_badge_if_not_exists(user, 'daily_streak_10')
        if user.current_streak >= 30:
            PointsService.award_badge_if_not_exists(user, 'daily_streak_30')

        db.session.commit()

class NewPointsService:
    """Service class for handling all points, XP, reliability, LB, and shares logic"""
    
    @staticmethod
    def deposit_to_lb(user, amount):
        """Deposit points to Liquidity Buffer"""
        if amount <= 0 or amount > user.points:
            return False
        user.points -= amount
        user.lb_deposit += amount
        return True

    @staticmethod
    def withdraw_from_lb(user, amount):
        """Withdraw points from Liquidity Buffer"""
        if amount <= 0 or amount > user.lb_deposit:
            return False
        user.points += amount
        user.lb_deposit -= amount
        return True

    @staticmethod
    def calculate_lb_yield(user):
        """Calculate daily yield from Liquidity Buffer"""
        total_lb = db.session.query(func.sum(User.lb_deposit)).scalar() or 0
        if total_lb == 0:
            return 0
        
        # Annual yield rate (4-8% as per the document)
        base_yield = 6  # 6% annual yield
        
        # Adjust yield based on market activity
        active_markets = Market.query.filter_by(resolved=False).count()
        yield_adjustment = min(2, active_markets / 10)  # Up to 2% bonus for active markets
        
        # Calculate daily yield
        daily_yield = (base_yield + yield_adjustment) / 365
        
        return (user.lb_deposit * daily_yield) / 100

    @staticmethod
    def update_reliability(user, was_correct):
        """Update reliability index based on prediction accuracy"""
        if was_correct:
            user.reliability_index = min(100.0, user.reliability_index + (20 / (1 + len(user.predictions))))
            user.xp += 10
        else:
            user.reliability_index = max(0.0, user.reliability_index - (10 / (1 + len(user.predictions))))

    @staticmethod
    def calculate_prediction_value(prediction):
        """Calculate current value of prediction shares"""
        if prediction.prediction == 'YES':
            return prediction.shares * prediction.market.yes_price
        return prediction.shares * prediction.market.no_price

    @staticmethod
    def calculate_prediction_investment(prediction):
        """Calculate total points invested in prediction"""
        return prediction.shares * prediction.average_price

    @staticmethod
    def calculate_liquidity_provider_shares(user, market):
        """Calculate liquidity provider shares"""
        lp = LiquidityProvider.query.filter_by(
            user_id=user.id,
            market_id=market.id
        ).first()
        if lp:
            return lp.shares
        return 0.0
