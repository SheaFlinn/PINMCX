from typing import Dict, Optional
from app.services.points_ledger import PointsLedger
from app.models import Market, User
from config import Config

class PointsTradeEngine:
    """
    A modular trade engine that handles all aspects of market trades:
    - Price calculation
    - Pool updates
    - Share minting
    - Points deduction
    - Ledger logging
    
    This engine is designed to be token-compatible and fully observable.
    """

    @staticmethod
    def execute_trade(user: User, market: Market, amount: float, outcome: bool) -> Dict[str, float]:
        """
        Executes a trade on the market.
        
        Args:
            user: User making the trade
            market: Market to trade on
            amount: Amount of points to trade
            outcome: True for YES trade, False for NO trade
            
        Returns:
            Dict containing:
            - price: Price per share
            - shares: Number of shares purchased
            
        Raises:
            ValueError: If trade amount is invalid
        """
        # Validate trade amount
        if amount < Config.MIN_TRADE_SIZE or amount > Config.MAX_TRADE_SIZE:
            raise ValueError(f"Trade amount must be between {Config.MIN_TRADE_SIZE} and {Config.MAX_TRADE_SIZE}")
            
        # Calculate price and shares
        total_pool = market.yes_pool + market.no_pool
        if outcome:
            price = market.no_pool / total_pool * amount
        else:
            price = market.yes_pool / total_pool * amount
        shares = amount / price

        # Update market pools
        if outcome:
            market.yes_pool += amount
        else:
            market.no_pool += amount
        
        # Recalculate odds after pool updates
        total = market.yes_pool + market.no_pool
        market.odds_yes = market.yes_pool / total if total > 0 else 0.5
        market.odds_no = market.no_pool / total if total > 0 else 0.5
        
        market.update_prices()

        # Deduct points from user
        user.points -= amount

        # Log trade to ledger
        PointsLedger.log_transaction(
            user=user,
            amount=-amount,
            transaction_type="trade",
            description=f"Trade on market {market.id} - {'YES' if outcome else 'NO'} - {amount:.2f} points"
        )

        # Return trade details
        return {
            "price": price,
            "shares": shares,
            "outcome": "YES" if outcome else "NO"
        }
