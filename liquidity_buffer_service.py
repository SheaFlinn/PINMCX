import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

class LiquidityBufferService:
    def __init__(self):
        self.MIN_DEPOSIT = 20.0
        self.MAX_DEPOSIT = 100.0
        self.WITHDRAWAL_WINDOW = 90  # 3 months in days

    @staticmethod
    def _load_liquidity_buffer() -> Dict[str, Any]:
        """Load liquidity buffer data from JSON file."""
        path = os.path.join("data", "liquidity_buffer.json")
        try:
            if not os.path.exists(path):
                return {}
            with open(path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _save_liquidity_buffer(data: Dict[str, Any]) -> None:
        """Save liquidity buffer data to JSON file."""
        path = os.path.join("data", "liquidity_buffer.json")
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def _load_wallet() -> Dict[str, Any]:
        """Load wallet data from JSON file."""
        path = os.path.join("data", "wallet.json")
        try:
            if not os.path.exists(path):
                return {}
            with open(path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _save_wallet(data: Dict[str, Any]) -> None:
        """Save wallet data to JSON file."""
        path = os.path.join("data", "wallet.json")
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def _log_action(action_type: str, user_id: str, amount: Optional[float] = None) -> None:
        """Log liquidity buffer actions."""
        try:
            os.makedirs("logs", exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("logs/liquidity_buffer.log", 'a') as f:
                if amount is not None:
                    f.write(f"[{timestamp}] {action_type} - User: {user_id}, Amount: ${amount:.2f}\n")
                else:
                    f.write(f"[{timestamp}] {action_type} - User: {user_id}\n")
        except Exception as e:
            print(f"❌ Error logging action: {str(e)}")

    @staticmethod
    def can_withdraw(user_id: str, current_date: datetime.date) -> bool:
        """Return True if it's been 90+ days since last withdrawal."""
        lb = LiquidityBufferService._load_liquidity_buffer()
        if user_id not in lb:
            return False
        
        last_withdrawal = lb[user_id].get("last_withdrawal")
        if not last_withdrawal:
            return True
            
        last_withdrawal_date = datetime.strptime(last_withdrawal, "%Y-%m-%d").date()
        return (current_date - last_withdrawal_date).days >= LiquidityBufferService.WITHDRAWAL_WINDOW

    @staticmethod
    def withdraw(user_id: str, current_date: datetime.date) -> float:
        """Withdraw entire balance to wallet if eligible."""
        if not LiquidityBufferService.can_withdraw(user_id, current_date):
            raise Exception("Withdrawal not allowed yet")

        # Load data
        lb = LiquidityBufferService._load_liquidity_buffer()
        wallet = LiquidityBufferService._load_wallet()

        # Get withdrawal amount
        amount = lb[user_id]["balance"]
        if amount <= 0:
            raise Exception("No balance available to withdraw")

        # Update wallet
        wallet[user_id] += amount
        LiquidityBufferService._save_wallet(wallet)

        # Update liquidity buffer
        lb[user_id] = {
            "balance": 0,
            "last_withdrawal": current_date.strftime("%Y-%m-%d")
        }
        LiquidityBufferService._save_liquidity_buffer(lb)

        # Log action
        LiquidityBufferService._log_action("WITHDRAW", user_id, amount)

        return amount

    @staticmethod
    def distribute_fees(total_fees: float) -> None:
        """Distribute 1% of total platform fees proportionally to LB contributors."""
        if not isinstance(total_fees, (int, float)) or total_fees <= 0:
            raise Exception("Total fees must be a positive number")

        # Calculate 1% of fees
        lb_contribution = total_fees * 0.01

        # Load liquidity buffer
        lb = LiquidityBufferService._load_liquidity_buffer()
        if not lb:
            return  # No users in LB, no distribution needed

        # Calculate total balance
        total_balance = sum(user_data["balance"] for user_data in lb.values())
        if total_balance <= 0:
            return  # No balance in LB, no distribution needed

        # Distribute proportionally
        for user_id, user_data in lb.items():
            share = user_data["balance"] / total_balance
            user_contribution = lb_contribution * share
            lb[user_id]["balance"] += user_contribution

        # Save updated liquidity buffer
        LiquidityBufferService._save_liquidity_buffer(lb)

        # Log action
        LiquidityBufferService._log_action("DISTRIBUTE_FEES", None, lb_contribution)

    def deposit(self, user_id: str, amount: float) -> None:
        """Process user deposit to liquidity buffer."""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Amount must be a positive number")
            
        if amount < self.MIN_DEPOSIT:
            raise ValueError(f"Minimum deposit is ${self.MIN_DEPOSIT}")
            
        if amount > self.MAX_DEPOSIT:
            raise ValueError(f"Maximum deposit is ${self.MAX_DEPOSIT}")

        # Load wallet and check balance
        wallet = self._load_wallet()
        if user_id not in wallet:
            raise ValueError(f"User {user_id} not found in wallet")
            
        if wallet[user_id] < amount:
            raise ValueError(f"Insufficient funds in wallet. Balance: ${wallet[user_id]}")

        # Update wallet
        wallet[user_id] -= amount
        self._save_wallet(wallet)

        # Load and update liquidity buffer
        lb = self._load_liquidity_buffer()
        if user_id not in lb:
            lb[user_id] = {
                "balance": 0,
                "last_withdrawal": None
            }
        
        lb[user_id]["balance"] += amount
        self._save_liquidity_buffer(lb)

    def get_total_liquidity(self) -> float:
        """Get total available liquidity in buffer."""
        lb = self._load_liquidity_buffer()
        return sum(user_data["balance"] for user_data in lb.values())

if __name__ == "__main__":
    import argparse
    import sys
    from datetime import datetime

    parser = argparse.ArgumentParser(description="Liquidity Buffer Service CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # New wallet initialization command
    init_parser = subparsers.add_parser("init", help="Initialize wallet with test users")
    init_parser.add_argument("--users", type=int, default=3, help="Number of test users to create")
    init_parser.add_argument("--balance", type=float, default=1000.0, help="Initial balance for each user")

    # Deposit command
    deposit_parser = subparsers.add_parser("deposit", help="Deposit funds to liquidity buffer")
    deposit_parser.add_argument("user_id", help="User ID")
    deposit_parser.add_argument("amount", type=float, help="Deposit amount")

    # Withdraw command
    withdraw_parser = subparsers.add_parser("withdraw", help="Withdraw funds from liquidity buffer")
    withdraw_parser.add_argument("user_id", help="User ID")
    withdraw_parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), 
                              help="Date for withdrawal check (YYYY-MM-DD)")

    # Check withdrawal eligibility
    check_parser = subparsers.add_parser("check", help="Check withdrawal eligibility")
    check_parser.add_argument("user_id", help="User ID")
    check_parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), 
                            help="Date to check eligibility (YYYY-MM-DD)")

    # Distribute fees
    fee_parser = subparsers.add_parser("distribute", help="Distribute platform fees")
    fee_parser.add_argument("amount", type=float, help="Total fees to distribute")

    # Get total liquidity
    total_parser = subparsers.add_parser("total", help="Get total liquidity")

    # Get wallet balance
    balance_parser = subparsers.add_parser("balance", help="Get user wallet balance")
    balance_parser.add_argument("user_id", help="User ID")

    args = parser.parse_args()
    service = LiquidityBufferService()

    try:
        if args.command == "init":
            wallet = service._load_wallet()
            for i in range(args.users):
                user_id = f"user_{i+1:03d}"
                if user_id not in wallet:
                    wallet[user_id] = args.balance
            service._save_wallet(wallet)
            print(f"✅ Initialized {args.users} test users with ${args.balance:.2f} each")

        elif args.command == "deposit":
            service.deposit(args.user_id, args.amount)
            print(f"✅ Deposited ${args.amount:.2f} for user {args.user_id}")

        elif args.command == "withdraw":
            amount = LiquidityBufferService.withdraw(args.user_id, datetime.strptime(args.date, "%Y-%m-%d").date())
            print(f"✅ Withdrew ${amount:.2f} for user {args.user_id}")

        elif args.command == "check":
            is_eligible = LiquidityBufferService.can_withdraw(args.user_id, datetime.strptime(args.date, "%Y-%m-%d").date())
            print(f"✅ User {args.user_id} is {'eligible' if is_eligible else 'not eligible'} to withdraw")

        elif args.command == "distribute":
            LiquidityBufferService.distribute_fees(args.amount)
            print(f"✅ Distributed fees to liquidity buffer")

        elif args.command == "total":
            total = service.get_total_liquidity()
            print(f"Total liquidity: ${total:.2f}")

        elif args.command == "balance":
            wallet = service._load_wallet()
            if args.user_id in wallet:
                print(f"User {args.user_id} balance: ${wallet[args.user_id]:.2f}")
            else:
                print(f"❌ User {args.user_id} not found in wallet")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
