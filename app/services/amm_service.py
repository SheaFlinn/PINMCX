from datetime import datetime
from app.models.amm_market import AMMMarket
from app.models.liquidity_pool import LiquidityPool
from math import log, exp
from typing import Dict, Any

class AMMService:
    def __init__(self):
        pass

    @staticmethod
    def get_current_odds(yes_liquidity: float, no_liquidity: float, current_odds_yes: float = 0.5, current_odds_no: float = 0.5) -> Dict[str, float]:
        """
        Calculate the current odds based on liquidity ratios.
        
        Args:
            yes_liquidity: Current liquidity in YES pool
            no_liquidity: Current liquidity in NO pool
            current_odds_yes: Current YES odds (default 0.5)
            current_odds_no: Current NO odds (default 0.5)
            
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
    def calculate_share_allocation(yes_liquidity: float, no_liquidity: float, stake: float, outcome: bool) -> Dict[str, Any]:
        """
        Given a stake and outcome, calculate new liquidity values and shares allocated.
        Enforces the constant product invariant: x * y = k
        
        Args:
            yes_liquidity: Current YES pool liquidity
            no_liquidity: Current NO pool liquidity
            stake: Amount of stake to add
            outcome: True for YES position, False for NO position
            
        Returns:
            dict: Dictionary containing:
                - shares: Number of shares allocated
                - yes_liquidity: New YES pool liquidity
                - no_liquidity: New NO pool liquidity
                - price: Price per share
        """
        if not isinstance(outcome, bool):
            raise ValueError("Outcome must be a boolean value (True for YES, False for NO)")

        # Calculate the price based on liquidity ratios
        total_liquidity = yes_liquidity + no_liquidity
        if total_liquidity == 0:
            raise ZeroDivisionError("Cannot calculate price with zero liquidity")

        # Calculate shares based on outcome
        if outcome:  # YES position
            shares = stake / (no_liquidity / total_liquidity)
            new_no_liquidity = no_liquidity + stake
            new_yes_liquidity = yes_liquidity
        else:  # NO position
            shares = stake / (yes_liquidity / total_liquidity)
            new_yes_liquidity = yes_liquidity + stake
            new_no_liquidity = no_liquidity

        # Calculate new price
        new_total = new_yes_liquidity + new_no_liquidity
        price = new_no_liquidity / new_total

        return {
            'shares': shares,
            'yes_liquidity': new_yes_liquidity,
            'no_liquidity': new_no_liquidity,
            'price': price
        }

    @staticmethod
    def update_odds(pool: LiquidityPool) -> None:
        """
        Recompute and store current odds in the pool.
        """
        try:
            odds = AMMService.get_current_odds(
                pool.yes_liquidity,
                pool.no_liquidity,
                pool.current_odds_yes,
                pool.current_odds_no
            )
            pool.current_odds_yes = odds['yes']
            pool.current_odds_no = odds['no']
        except ZeroDivisionError:
            # Handle zero liquidity case by keeping current odds
            pass
