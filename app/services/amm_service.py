from datetime import datetime
from app.models.amm_market import AMMMarket
from app.models.liquidity_pool import LiquidityPool
from app.models.prediction import Prediction
from math import log, exp
from typing import Dict, Any
from sqlalchemy import func

class AMMService:
    def __init__(self):
        pass

    @staticmethod
    def get_current_odds(yes_liquidity: float, no_liquidity: float) -> Dict[str, float]:
        """
        Calculate the current odds based on liquidity ratios.
        
        Args:
            yes_liquidity: Current YES pool liquidity
            no_liquidity: Current NO pool liquidity
            
        Returns:
            dict: Dictionary containing 'yes' and 'no' odds
            
        Raises:
            ZeroDivisionError: If total liquidity is zero
        """
        total = yes_liquidity + no_liquidity
        if total == 0:
            raise ZeroDivisionError("Cannot calculate odds with zero liquidity")

        return {
            'yes': no_liquidity / total,
            'no': yes_liquidity / total
        }

    @staticmethod
    def calculate_share_allocation(amount: float, outcome: bool, market_id: int) -> Dict[str, Any]:
        """
        Calculate share allocation using Logarithmic Market Scoring Rule (LMSR).
        
        Args:
            amount: Amount of points to stake
            outcome: True for YES, False for NO
            market_id: ID of the market
        
        Returns:
            dict: Dictionary containing:
                - shares: Number of shares purchased
                - cost_before: Cost before purchase
                - cost_after: Cost after purchase
                - price: Price per share
        
        Raises:
            TypeError: If outcome is not a boolean
        """
        if not isinstance(outcome, bool):
            raise TypeError("Outcome must be a boolean value (True for YES, False for NO)")

        # Define liquidity constant
        b = 10.0

        # Fetch total shares for each outcome
        yes_shares = Prediction.query.filter_by(
            market_id=market_id,
            outcome=True
        ).with_entities(func.sum(Prediction.shares_purchased)).scalar() or 0

        no_shares = Prediction.query.filter_by(
            market_id=market_id,
            outcome=False
        ).with_entities(func.sum(Prediction.shares_purchased)).scalar() or 0

        # Calculate initial cost
        cost_before = b * log(exp(yes_shares / b) + exp(no_shares / b))

        # Calculate shares to purchase using binary search
        low = 0
        high = amount  # Upper bound is amount since cost can't exceed amount
        delta = 0
        
        # Binary search to find delta that matches the cost
        for _ in range(30):  # Maximum iterations
            delta = (low + high) / 2
            
            # Calculate cost with delta added to the chosen outcome
            if outcome:
                new_cost = b * log(exp((yes_shares + delta) / b) + exp(no_shares / b))
            else:
                new_cost = b * log(exp(yes_shares / b) + exp((no_shares + delta) / b))
            
            current_cost = new_cost - cost_before
            
            if abs(current_cost - amount) < 1e-6:  # Close enough
                break
            
            if current_cost < amount:
                low = delta
            else:
                high = delta

        # Calculate final cost and price
        if outcome:
            cost_after = b * log(exp((yes_shares + delta) / b) + exp(no_shares / b))
        else:
            cost_after = b * log(exp(yes_shares / b) + exp((no_shares + delta) / b))

        price = amount / delta

        return {
            'shares': delta,
            'cost_before': cost_before,
            'cost_after': cost_after,
            'price': price
        }

    @classmethod
    def price_contract(cls, market_id: int) -> Dict[str, float]:
        """
        Calculate implied odds for a YES/NO market based on current prediction volume.
        
        Args:
            market_id: ID of the market to price
            
        Returns:
            dict: {
                "yes": float,  # Probability of YES outcome (0.0 to 1.0)
                "no": float     # Probability of NO outcome (0.0 to 1.0)
            }
            
        Notes:
            - If no predictions exist, returns default 50/50 odds
            - Odds always sum to 1.0
        """
        from app.models import Prediction
        
        # Get all predictions for this market
        predictions = Prediction.query.filter_by(market_id=market_id).all()
        if not predictions:
            return {"yes": 0.5, "no": 0.5}
            
        # Calculate totals
        yes_total = sum(p.stake for p in predictions if p.outcome)
        no_total = sum(p.stake for p in predictions if not p.outcome)
        
        # Calculate odds
        total = yes_total + no_total
        if total == 0:
            return {"yes": 0.5, "no": 0.5}
            
        # Return odds rounded to 4 decimal places
        return {
            "yes": round(yes_total / total, 4),
            "no": round(no_total / total, 4)
        }

    @staticmethod
    def update_odds(pool: LiquidityPool) -> None:
        """
        Update the pool's current odds based on current liquidity.
        
        Args:
            pool: Liquidity pool object with yes_liquidity and no_liquidity
        """
        odds = AMMService.get_current_odds(pool.yes_liquidity, pool.no_liquidity)
        pool.current_odds_yes = odds['yes']
        pool.current_odds_no = odds['no']
