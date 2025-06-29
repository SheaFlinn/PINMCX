from app import db
from .points_ledger import PointsLedger

class PointsPayoutEngine:
    """Service for handling point payouts and managing user balances"""
    
    @staticmethod
    def award_trade_payout(user, amount: float, market_id: int, outcome: str) -> None:
        """
        Handle point payout for a market trade
        
        Args:
            user: User receiving the payout
            amount: Amount of points to award
            market_id: ID of the market being traded
            outcome: Outcome of the trade ('YES' or 'NO')
        """
        from app.models import User
        # Update user's points balance
        user.points += amount
        
        # Log the transaction
        PointsLedger.log_transaction(
            user_id=user.id,
            amount=amount,
            transaction_type='trade',
            description=f"Trade payout for market {market_id} - {outcome}"
        )
        
        # Commit changes
        db.session.commit()
    
    @staticmethod
    def award_resolution_payout(user, amount: float, market_id: int) -> None:
        """
        Handle point payout for market resolution
        
        Args:
            user: User receiving the payout
            amount: Amount of points to award
            market_id: ID of the resolved market
        """
        if amount <= 0:
            return
            
        # Update user's points and XP
        user.points += amount
        # Award XP based on payout amount, converting float to int
        xp_awarded = int(amount)
        user.xp += xp_awarded
        
        # Log the transaction
        PointsLedger.log_transaction(
            user_id=user.id,
            amount=amount,
            transaction_type='resolution',
            description=f"Resolution payout for market {market_id} - XP: {xp_awarded}"
        )
        
        # Commit changes
        db.session.commit()
