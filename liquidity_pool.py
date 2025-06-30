import json
import os
from typing import Dict, Any, Optional

POOL_FILE = "data/liquidity_pools.json"
DEFAULT_CAP = 250000

class LiquidityPoolService:
    @staticmethod
    def load_pools() -> Dict[str, Any]:
        """Load pools from JSON file."""
        try:
            os.makedirs(os.path.dirname(POOL_FILE), exist_ok=True)
            if not os.path.exists(POOL_FILE):
                return {}
            
            with open(POOL_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
        except Exception as e:
            print(f"❌ Error loading pools: {str(e)}")
            return {}

    @staticmethod
    def save_pools(pools: Dict[str, Any]) -> None:
        """Save pools to JSON file."""
        try:
            os.makedirs(os.path.dirname(POOL_FILE), exist_ok=True)
            with open(POOL_FILE, 'w') as f:
                json.dump(pools, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving pools: {str(e)}")

    @staticmethod
    def init_pool(contract_title: str, cap: int = DEFAULT_CAP) -> None:
        """Initialize a new liquidity pool for a contract."""
        pools = LiquidityPoolService.load_pools()
        if contract_title not in pools:
            pools[contract_title] = {
                "cap": cap,
                "yes_liquidity": cap / 2,
                "no_liquidity": cap / 2
            }
            LiquidityPoolService.save_pools(pools)
            print(f"✅ Initialized liquidity pool for contract: {contract_title}")
        else:
            print(f"⚠️ Pool already exists for contract: {contract_title}")

    @staticmethod
    def get_pool(contract_title: str) -> Optional[Dict[str, Any]]:
        """Get pool status for a contract."""
        pools = LiquidityPoolService.load_pools()
        return pools.get(contract_title)

    @staticmethod
    def apply_trade(contract_title: str, position: str, amount: float) -> None:
        """Apply a trade to the pool, updating liquidity."""
        pools = LiquidityPoolService.load_pools()
        pool = pools.get(contract_title)
        if not pool:
            raise Exception(f"Pool not found for contract: {contract_title}")

        if position == "YES":
            if pool["yes_liquidity"] < amount:
                raise Exception(f"Not enough YES liquidity. Available: ${pool['yes_liquidity']}")
            pool["yes_liquidity"] -= amount
        elif position == "NO":
            if pool["no_liquidity"] < amount:
                raise Exception(f"Not enough NO liquidity. Available: ${pool['no_liquidity']}")
            pool["no_liquidity"] -= amount
        else:
            raise Exception("Invalid position. Must be 'YES' or 'NO'")

        LiquidityPoolService.save_pools(pools)
        print(f"✅ Liquidity updated: {contract_title} → YES=${pool['yes_liquidity']:.2f} | NO=${pool['no_liquidity']:.2f}")

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Liquidity Pool Service CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Initialize pool command
    init_parser = subparsers.add_parser("init", help="Initialize a new liquidity pool")
    init_parser.add_argument("contract_title", help="Contract title to initialize pool for")
    init_parser.add_argument("--cap", type=int, default=DEFAULT_CAP, help="Pool cap amount")

    # Get pool command
    get_parser = subparsers.add_parser("get", help="Get pool status")
    get_parser.add_argument("contract_title", help="Contract title to get pool status for")

    # Apply trade command
    trade_parser = subparsers.add_parser("trade", help="Apply trade to pool")
    trade_parser.add_argument("contract_title", help="Contract title")
    trade_parser.add_argument("position", choices=["YES", "NO"], help="Trade position")
    trade_parser.add_argument("amount", type=float, help="Trade amount")

    # List all pools command
    list_parser = subparsers.add_parser("list", help="List all pools")

    args = parser.parse_args()

    try:
        if args.command == "init":
            LiquidityPoolService.init_pool(args.contract_title, args.cap)

        elif args.command == "get":
            pool = LiquidityPoolService.get_pool(args.contract_title)
            if pool:
                print(f"Pool for {args.contract_title}:")
                print(f"  Cap: ${pool['cap']}")
                print(f"  YES Liquidity: ${pool['yes_liquidity']:.2f}")
                print(f"  NO Liquidity: ${pool['no_liquidity']:.2f}")
            else:
                print(f"❌ Pool not found for {args.contract_title}")

        elif args.command == "trade":
            LiquidityPoolService.apply_trade(args.contract_title, args.position, args.amount)

        elif args.command == "list":
            pools = LiquidityPoolService.load_pools()
            if not pools:
                print("No pools found")
            else:
                print("=== All Liquidity Pools ===")
                for title, pool in pools.items():
                    print(f"\n{title}")
                    print(f"  Cap: ${pool['cap']}")
                    print(f"  YES Liquidity: ${pool['yes_liquidity']:.2f}")
                    print(f"  NO Liquidity: ${pool['no_liquidity']:.2f}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
