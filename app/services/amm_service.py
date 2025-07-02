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
    def calculate_share_allocation(yes_liquidity: float, no_liquidity: float, stake: float, outcome: str) -> Dict[str, Any]:
        """
        Given a stake and outcome, calculate new liquidity values and shares allocated.
        Enforces the constant product invariant: x * y = k
        
        Args:
            yes_liquidity: Current YES pool liquidity
            no_liquidity: Current NO pool liquidity
            stake: Amount of stake to add
            outcome: 'YES' or 'NO' position
            
        Returns:
            dict: Dictionary containing:
                - yes_liquidity: New YES pool liquidity
                - no_liquidity: New NO pool liquidity
                - shares_purchased: Number of shares allocated
                - price: Price paid per share
                - slippage: Percentage slippage from initial odds
            
        Raises:
            ValueError: If outcome is not 'YES' or 'NO'
            ZeroDivisionError: If liquidity is zero or negative
        """
        if yes_liquidity <= 0 or no_liquidity <= 0:
            raise ZeroDivisionError("Cannot calculate allocation with zero or negative liquidity")

        k = yes_liquidity * no_liquidity
        initial_odds = AMMService.get_current_odds(yes_liquidity, no_liquidity)

        if outcome.upper() == "YES":
            new_yes_liquidity = yes_liquidity + stake
            new_no_liquidity = k / new_yes_liquidity
            shares_purchased = no_liquidity - new_no_liquidity
            price = stake / shares_purchased
            
        elif outcome.upper() == "NO":
            new_no_liquidity = no_liquidity + stake
            new_yes_liquidity = k / new_no_liquidity
            shares_purchased = yes_liquidity - new_yes_liquidity
            price = stake / shares_purchased
            
        else:
            raise ValueError("Invalid outcome. Must be 'YES' or 'NO'.")

        # Calculate slippage
        final_odds = AMMService.get_current_odds(new_yes_liquidity, new_no_liquidity)
        if outcome.upper() == "YES":
            slippage = ((final_odds['yes'] - initial_odds['yes']) / initial_odds['yes']) * 100
        else:
            slippage = ((final_odds['no'] - initial_odds['no']) / initial_odds['no']) * 100

        return {
            'yes_liquidity': new_yes_liquidity,
            'no_liquidity': new_no_liquidity,
            'shares_purchased': shares_purchased,
            'price': price,
            'slippage': abs(slippage)
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
