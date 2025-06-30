import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from liquidity_buffer_service import LiquidityBufferService
from liquidity_pool import LiquidityPoolService

POOL_FILE = "data/liquidity_pools.json"

class MockWallet:
    def __init__(self):
        self.balance = 10000  # Starting balance in points
        self.shares = {}  # contract_title -> {"yes": int, "no": int}

    def deduct_points(self, amount: int) -> bool:
        """Deduct points from wallet with 5% entry fee."""
        fee = amount * 0.05
        total_cost = amount + fee
        if self.balance >= total_cost:
            self.balance -= total_cost
            return True
        return False

class TradeEngine:
    def __init__(self):
        self.wallet = MockWallet()
        self.trade_log = []
        self.live_contracts_path = "live/priced_contracts.json"
        self.trade_log_path = "logs/trade_log.json"

        required_dirs = [
            os.path.dirname(self.live_contracts_path),
            os.path.dirname(self.trade_log_path),
            os.path.dirname(POOL_FILE)
        ]
        for dir_path in required_dirs:
            os.makedirs(dir_path, exist_ok=True)

        for file_path in [self.live_contracts_path, self.trade_log_path, POOL_FILE]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump([] if "contracts" in file_path else {}, f, indent=2)

    def _load_contracts(self) -> List[Dict[str, Any]]:
        try:
            if not os.path.exists(self.live_contracts_path):
                return []
            with open(self.live_contracts_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _save_contracts(self, contracts: List[Dict[str, Any]]) -> None:
        with open(self.live_contracts_path, 'w') as f:
            json.dump(contracts, f, indent=2)

    def _find_contract(self, contract_title: str) -> Optional[Dict[str, Any]]:
        contracts = self._load_contracts()
        return next((c for c in contracts if c.get("title") == contract_title), None)

    def _find_or_create_contract(self, contract_title: str) -> Dict[str, Any]:
        contract = self._find_contract(contract_title)
        if contract:
            return contract
        new_contract = {
            "title": contract_title,
            "total_yes": 0,
            "total_no": 0,
            "odds_yes": 0.5,
            "odds_no": 0.5,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        contracts = self._load_contracts()
        contracts.append(new_contract)
        self._save_contracts(contracts)
        return new_contract

    def _update_contract(self, contract_title: str, updates: Dict[str, Any]) -> None:
        contracts = self._load_contracts()
        for contract in contracts:
            if contract.get("title") == contract_title:
                contract.update(updates)
                break
        self._save_contracts(contracts)

    def process_trade(self, contract_title: str, position: str, points: int) -> Optional[Dict[str, Any]]:
        if position not in ["YES", "NO"]:
            return None

        contract = self._find_or_create_contract(contract_title)
        if not contract:
            return None

        LiquidityPoolService.init_pool(contract_title, cap=1000)
        pool = LiquidityPoolService.get_pool(contract_title)
        if not pool:
            return None

        yes_liq = pool["yes_liquidity"]
        no_liq = pool["no_liquidity"]

        odds_before = {
            "yes": round(no_liq / (yes_liq + no_liq), 4),
            "no": round(yes_liq / (yes_liq + no_liq), 4)
        }

        if not self.wallet.deduct_points(points):
            return None

        LiquidityPoolService.apply_trade(contract_title, position, points)
        pool = LiquidityPoolService.get_pool(contract_title)
        yes_liq = pool["yes_liquidity"]
        no_liq = pool["no_liquidity"]

        odds_after = {
            "yes": round(no_liq / (yes_liq + no_liq), 4),
            "no": round(yes_liq / (yes_liq + no_liq), 4)
        }

        position = position.lower()
        new_yes = contract.get("total_yes", 0) + (points if position == "yes" else 0)
        new_no = contract.get("total_no", 0) + (points if position == "no" else 0)

        self._update_contract(contract_title, {
            "total_yes": new_yes,
            "total_no": new_no,
