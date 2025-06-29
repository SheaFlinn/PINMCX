from datetime import datetime
from app import db
from app.models import User, UserLedger

class PointsLedger:
    """Service for tracking and logging all point transactions"""
    
    @staticmethod
    def log_transaction(user_id: int, amount: float, transaction_type: str, description: str = None) -> None:
        """
        Log a point transaction in the ledger
        
        Args:
            user_id: ID of the user involved in the transaction
            amount: Amount of points (positive for credit, negative for debit)
            transaction_type: Type of transaction (e.g., 'trade', 'resolution', 'xp')
            description: Optional description of the transaction
        """
        # Create a ledger entry
        ledger_entry = UserLedger(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description or f"{transaction_type} transaction"
        )
        db.session.add(ledger_entry)
        db.session.commit()

    @staticmethod
    def get_user_balance(user: 'User') -> float:
        """Get user's current point balance"""
        return user.points

    @staticmethod
    def get_transaction_history(user: 'User', limit: int = 10) -> list:
        """Get user's transaction history"""
        return UserLedger.query.filter_by(user_id=user.id).order_by(UserLedger.created_at.desc()).limit(limit).all()
