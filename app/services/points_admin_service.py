from typing import Optional
from datetime import datetime
from app.models import User, Market, Badge, UserBadge, db, generate_contract_hash
from app.services.points_ledger import PointsLedger
from config import Config

class PointsAdminService:
    """
    Service for admin-level point controls and overrides.
    All methods log to PointsLedger with transaction_type="admin_manual"
    """

    @staticmethod
    def award_manual_xp(user: User, amount: int, reason: str) -> None:
        """
        Award manual XP to a user.
        
        Args:
            user: User to award XP to
            amount: Amount of XP to award
            reason: Reason for XP award
            
        Raises:
            ValueError: If amount is negative or reason is empty
        """
        if amount <= 0:
            raise ValueError("XP amount must be positive")
        if not reason.strip():
            raise ValueError("Reason cannot be empty")

        user.xp += amount
        PointsLedger.log_transaction(
            user=user,
            amount=amount,
            transaction_type="admin_manual",
            description=f"Admin XP award - {reason}"
        )
        print(f"✅ Awarded {amount} XP to {user.username} for: {reason}")

    @staticmethod
    def adjust_liquidity_buffer(user: User, amount: float, direction: str) -> None:
        """
        Adjust user's liquidity buffer deposit.
        
        Args:
            user: User to adjust
            amount: Amount to adjust
            direction: 'deposit' or 'withdraw'
            
        Raises:
            ValueError: If direction is invalid or amount is negative
        """
        if direction not in ['deposit', 'withdraw']:
            raise ValueError("Direction must be 'deposit' or 'withdraw'")
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if direction == 'deposit':
            user.lb_deposit += amount
            action = "deposited"
        else:
            if user.lb_deposit < amount:
                raise ValueError("Cannot withdraw more than current deposit")
            user.lb_deposit -= amount
            action = "withdrawn"

        PointsLedger.log_transaction(
            user=user,
            amount=amount if direction == 'deposit' else -amount,
            transaction_type="admin_manual",
            description=f"Liquidity buffer {action}: {amount}"
        )
        print(f"✅ {action.title()} {amount} points to liquidity buffer for {user.username}")

    @staticmethod
    def credit_points(user: User, amount: float, reason: str) -> None:
        """
        Credit points to user's balance.
        
        Args:
            user: User to credit
            amount: Amount to credit
            reason: Reason for credit
            
        Raises:
            ValueError: If amount is negative or reason is empty
        """
        if amount <= 0:
            raise ValueError("Credit amount must be positive")
        if not reason.strip():
            raise ValueError("Reason cannot be empty")

        user.points += amount
        PointsLedger.log_transaction(
            user=user,
            amount=amount,
            transaction_type="admin_manual",
            description=f"Admin point credit - {reason}"
        )
        print(f"✅ Credited {amount} points to {user.username} for: {reason}")

    @staticmethod
    def debit_points(user: User, amount: float, reason: str) -> None:
        """
        Debit points from user's balance.
        
        Args:
            user: User to debit
            amount: Amount to debit
            reason: Reason for debit
            
        Raises:
            ValueError: If amount is negative or reason is empty
        """
        if amount <= 0:
            raise ValueError("Debit amount must be positive")
        if not reason.strip():
            raise ValueError("Reason cannot be empty")
        if user.points < amount:
            raise ValueError(f"Insufficient points: user has {user.points}, requested {amount}")

        user.points -= amount
        PointsLedger.log_transaction(
            user=user,
            amount=-amount,
            transaction_type="admin_manual",
            description=f"Admin point debit - {reason}"
        )
        print(f"✅ Debited {amount} points from {user.username} for: {reason}")

    @staticmethod
    def force_resolve_market(market: Market, outcome: str, admin_user_id: int) -> None:
        """
        Force resolve a market to a specific outcome.
        
        Args:
            market: Market to resolve
            outcome: 'YES' or 'NO'
            admin_user_id: ID of admin performing the action
            
        Raises:
            ValueError: If outcome is invalid
        """
        if outcome not in ['YES', 'NO']:
            raise ValueError("Outcome must be 'YES' or 'NO'")

        # Resolve market
        market.resolved = True
        market.resolved_outcome = outcome
        market.resolved_at = datetime.utcnow()
        market.integrity_hash = generate_contract_hash(market)

        # Log to ledger
        PointsLedger.log_transaction(
            user_id=admin_user_id,
            amount=0,
            transaction_type="admin_manual",
            description=f"Admin forced market {market.id} resolution to {outcome}"
        )
        print(f"✅ Forced resolution of market {market.id} to {outcome}")

    @staticmethod
    def grant_badge(user: User, badge: Badge, reason: str) -> None:
        """
        Grants a badge to a user and logs the action.

        Args:
            user: The user receiving the badge
            badge: The badge being granted
            reason: Reason or context for the badge
        """
        from app.models import UserBadge, db

        # Check if already has badge
        existing = UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first()
        if existing:
            print(f"⚠️  User {user.username} already has badge {badge.name}")
            return

        user_badge = UserBadge(user=user, badge=badge)
        db.session.add(user_badge)
        db.session.commit()  # Commit the badge assignment

        PointsLedger.log_transaction(
            user_id=user.id,
            amount=0,
            transaction_type="badge_awarded",
            description=f"Badge '{badge.name}' granted. Reason: {reason}"
        )
        print(f"✅ Granted badge {badge.name} to {user.username}")
