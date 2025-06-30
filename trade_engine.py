<<<<<<< HEAD
from app.models import Market, Prediction, User
from app import db
from config import Config
=======
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from liquidity_buffer_service import LiquidityBufferService
from liquidity_pool import LiquidityPoolService

POOL_FILE = "data/liquidity_pools.json"
>>>>>>> 21d58c6 (♻️ Update trading engine and publisher to reflect new AMM and liquidity flow)

def execute_trade(user: User, market: Market, amount: float, outcome: str):
    if market.resolved:
        raise ValueError("Cannot trade on a resolved market.")

    if amount < Config.MIN_TRADE_SIZE or amount > Config.MAX_TRADE_SIZE:
        raise ValueError("Trade amount out of bounds.")

<<<<<<< HEAD
    # Fee routing
    fee = amount * Config.LIQUIDITY_FEE_RATE
    net_amount = amount - fee
    user.points -= amount
    user.lb_deposit += fee  # Add fee to LB (simplified logic)

    # Pricing
    if outcome == 'YES':
        price = market.yes_pool / market.no_pool
        shares = net_amount / price
        market.yes_pool += net_amount
    elif outcome == 'NO':
        price = market.no_pool / market.yes_pool
        shares = net_amount / price
        market.no_pool += net_amount
=======
class TradeEngine:
    def __init__(self):
        self.wallet = MockWallet()
        self.trade_log = []
        self.live_contracts_path = "live/priced_contracts.json"
        self.trade_log_path = "logs/trade_log.json"
        
        # Create required directories
        required_dirs = [
            os.path.dirname(self.live_contracts_path),
            os.path.dirname(self.trade_log_path),
            os.path.dirname(POOL_FILE)
        ]
        
        for dir_path in required_dirs:
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Created directory: {dir_path}")
        
        # Initialize empty files if they don't exist
        for file_path in [self.live_contracts_path, self.trade_log_path, POOL_FILE]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump([], f if file_path != POOL_FILE else {}, f, indent=2)
                print(f"✅ Created file: {file_path}")

    def _load_contracts(self) -> List[Dict[str, Any]]:
        """Safely load contracts from JSON file."""
        try:
            if not os.path.exists(self.live_contracts_path):
                return []  # Start with empty list if file doesn't exist
            with open(self.live_contracts_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _save_contracts(self, contracts: List[Dict[str, Any]]) -> None:
        """Safely save contracts to JSON file."""
        with open(self.live_contracts_path, 'w') as f:
            json.dump(contracts, f, indent=2)

    def _find_contract(self, contract_title: str) -> Optional[Dict[str, Any]]:
        """Find contract by title in list of contracts."""
        contracts = self._load_contracts()
        if not contracts:
            print("❌ Warning: No contracts found in priced_contracts.json")
            return None
        
        contract = next((c for c in contracts if c.get("title") == contract_title), None)
        if not contract:
            print(f"❌ Warning: Contract with title '{contract_title}' not found in {len(contracts)} contracts")
        return contract

    def _find_or_create_contract(self, contract_title: str) -> Dict[str, Any]:
        """Find or create a contract with default values."""
        contract = self._find_contract(contract_title)
        if contract:
            return contract

        # Create new contract with default values
        new_contract = {
            "title": contract_title,
            "total_yes": 0,
            "total_no": 0,
            "odds_yes": 0.5,
            "odds_no": 0.5,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Add to contracts
        contracts = self._load_contracts()
        contracts.append(new_contract)
        self._save_contracts(contracts)
        
        print(f"✅ Created new contract: {contract_title}")
        return new_contract

    def _update_contract(self, contract_title: str, updates: Dict[str, Any]) -> None:
        """Update a specific contract in the list."""
        contracts = self._load_contracts()
        for contract in contracts:
            if contract.get("title") == contract_title:
                contract.update(updates)
                break
        self._save_contracts(contracts)

    def process_trade(self, contract_title: str, position: str, points: int) -> Optional[Dict[str, Any]]:
        """Process a trade on a specific contract."""
        if position not in ["YES", "NO"]:
            print(f"❌ Error: Invalid position '{position}'. Must be either 'YES' or 'NO'")
            return None

        print(f"🔍 Processing trade: Contract={contract_title}, Position={position}, Points={points}")
        
        # Get or create contract
        contract = self._find_or_create_contract(contract_title)
        if not contract:
            print(f"❌ Error: Failed to create contract {contract_title}")
            return None

        print(f"✅ Found or created contract: {contract}")

        # Initialize pool if it doesn't exist
        try:
            LiquidityPoolService.init_pool(contract_title, cap=1000)
        except Exception as e:
            print(f"❌ Error initializing pool: {str(e)}")
            return None

        # Load the liquidity pool for this contract
        try:
            pool = LiquidityPoolService.get_pool(contract_title)
            if not pool:
                print(f"❌ No liquidity pool found for contract: {contract_title}")
                return None

            yes_liq = pool["yes_liquidity"]
            no_liq = pool["no_liquidity"]
            cap = pool["cap"]

            # Calculate current odds (before trade)
            odds_before = {
                "yes": round(no_liq / (yes_liq + no_liq), 4),
                "no": round(yes_liq / (yes_liq + no_liq), 4)
            }

            # Check if user has enough points
            if not self.wallet.deduct_points(points):
                print(f"❌ Error: Insufficient funds. Balance={self.wallet.balance}, Cost={points * 1.05}")
                return None

            print(f"✅ Deducted points. New balance: {self.wallet.balance}")

            # Apply trade to pool
            try:
                LiquidityPoolService.apply_trade(contract_title, position, points)
                pool = LiquidityPoolService.get_pool(contract_title)  # Get updated pool state
                yes_liq = pool["yes_liquidity"]
                no_liq = pool["no_liquidity"]
            except Exception as e:
                print(f"❌ Error applying trade: {str(e)}")
                return None

            # Calculate updated odds (after trade)
            odds_after = {
                "yes": round(no_liq / (yes_liq + no_liq), 4),
                "no": round(yes_liq / (yes_liq + no_liq), 4)
            }

            # Update contract totals
            position = position.lower()
            current_yes = contract.get("total_yes", 0)
            current_no = contract.get("total_no", 0)
            
            # Update totals with new points
            new_yes = current_yes + (points if position == "yes" else 0)
            new_no = current_no + (points if position == "no" else 0)
            
            # Prepare updates
            updates = {
                "total_yes": new_yes,
                "total_no": new_no,
                "odds_yes": odds_after["yes"],
                "odds_no": odds_after["no"]
            }
            
            # Update contract
            self._update_contract(contract_title, updates)
            print(f"✅ Updated contract with: {updates}")

            # Record shares
            if contract_title not in self.wallet.shares:
                self.wallet.shares[contract_title] = {"yes": 0, "no": 0}
            self.wallet.shares[contract_title][position] += points

            # Log trade
            trade_log_entry = {
                "timestamp": datetime.now().isoformat(),
                "contract_title": contract_title,
                "position": position.upper(),
                "points": points,
                "entry_fee": points * 0.05,
                "total_cost": points * 1.05,
                "odds_before": odds_before,
                "odds_after": odds_after,
                "liquidity_before": pool.copy(),  # Log current pool state
                "user_balance": self.wallet.balance
            }
            self.trade_log.append(trade_log_entry)
            self._save_trade_log()
            print(f"✅ Logged trade: {trade_log_entry}")

            # Distribute 1% of entry fee to Liquidity Buffer
            fee_share = points * 0.05 * 0.01
            LiquidityBufferService.distribute_fees(fee_share)
            print(f"✅ Distributed ${fee_share:.2f} from entry fee to Liquidity Buffer")

            return trade_log_entry

        except Exception as e:
            print(f"❌ Error processing trade: {str(e)}")
            return None

    def get_wallet_state(self) -> Dict[str, Any]:
        """Get current wallet state."""
        return {
            "balance": self.wallet.balance,
            "shares": self.wallet.shares
        }

    def _save_trade_log(self) -> None:
        """Save trade log to JSON file."""
        with open(self.trade_log_path, 'w') as f:
            json.dump(self.trade_log, f, indent=2, default=str)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Process a trade on a prediction market contract',
        epilog='Example: python3 trade_engine.py "Will the fundraising for the Liberty Stadium renovation in Memphis be completed by December 31, 2025?" YES 100\n' +
               'Note: Use quotes around contract titles containing spaces',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'contract_title', 
        type=str, 
        help='Title of the contract to trade (e.g., "Will the fundraising for the Liberty Stadium renovation in Memphis be completed by December 31, 2025?")'
    )
    parser.add_argument(
        'position', 
        type=str, 
        choices=['YES', 'NO'], 
        help='Trade position - must be either YES or NO'
    )
    parser.add_argument(
        'points', 
        type=int, 
        help='Number of points to trade (must be a positive integer)'
    )
    
    try:
        args = parser.parse_args()
    except SystemExit as e:
        print("❌ Error: Invalid arguments")
        print("Please run with exactly three arguments:")
        print("1. Contract title (use quotes if it contains spaces)")
        print("2. Position (YES or NO)")
        print("3. Points (positive integer)")
        print("\nExample: python3 trade_engine.py \"Will the fundraising for the Liberty Stadium renovation in Memphis be completed by December 31, 2025?\" YES 100")
        sys.exit(1)
    
    if args.points <= 0:
        print("❌ Error: Points must be a positive integer")
        sys.exit(1)
    
    print("\n=== Starting Trade Engine ===")
    engine = TradeEngine()
    print(f"Initial wallet state: {engine.get_wallet_state()}")
    
    result = engine.process_trade(args.contract_title, args.position, args.points)
    
    if result:
        print("\n=== Trade Successful ===")
        print("Trade details:", json.dumps(result, indent=2))
        print("\nFinal wallet state:", json.dumps(engine.get_wallet_state(), indent=2))
>>>>>>> 21d58c6 (♻️ Update trading engine and publisher to reflect new AMM and liquidity flow)
    else:
        raise ValueError("Invalid outcome side.")

    # Save prediction
    prediction = Prediction(user_id=user.id, market_id=market.id,
                            prediction=outcome, shares=shares,
                            average_price=price)
    db.session.add(prediction)
    db.session.commit()

    return {
        "price": price,
        "shares": shares,
        "fee_routed_to_LB": fee
    }
