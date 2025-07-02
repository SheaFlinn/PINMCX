from datetime import datetime, timedelta
from app.models import User, MarketEvent
from app import db

class LiquidityService:
    """
    Service for managing user liquidity buffer deposits and withdrawals.
    Implements a 90-day lockout period for withdrawals after deposits.
    """
    
    @classmethod
    def deposit(cls, user: User, amount: float) -> None:
        """
        Deposit liquidity into user's buffer.
        
        Args:
            user: User to deposit for
            amount: Amount to deposit (must be positive)
            
        Raises:
            ValueError: If amount is not positive
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
            
        # Update user's buffer and last deposit time
        user.liquidity_buffer_deposit += amount
        user.liquidity_last_deposit_at = datetime.utcnow()
        
        # Log the deposit
        MarketEvent.log_liquidity_deposit(
            user_id=user.id,
            amount=amount
        )
        
        # Commit changes
        db.session.add(user)
        db.session.commit()

    @classmethod
    def withdraw(cls, user: User, amount: float) -> None:
        """
        Withdraw liquidity from user's buffer.
        
        Args:
            user: User to withdraw from
            amount: Amount to withdraw (must be positive)
            
        Raises:
            ValueError: If amount is not positive
            ValueError: If withdrawal would exceed available balance
            ValueError: If trying to withdraw within 90 days of last deposit
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
            
        # Check if user has a deposit
        if not user.liquidity_last_deposit_at:
            raise ValueError("Cannot withdraw liquidity without a deposit")
            
        # Check 90-day lockout period
        if (datetime.utcnow() - user.liquidity_last_deposit_at) < timedelta(days=90):
            raise ValueError("Cannot withdraw liquidity within 90 days of last deposit")
            
        # Check sufficient funds
        if amount > user.liquidity_buffer_deposit:
            raise ValueError("Insufficient liquidity buffer balance")
            
        # Update user's buffer
        user.liquidity_buffer_deposit -= amount
        
        # Log the withdrawal
        MarketEvent.log_liquidity_withdraw(
            user_id=user.id,
            amount=amount
        )
        
        # Commit changes
        db.session.add(user)
        db.session.commit()
