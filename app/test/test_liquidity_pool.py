import os
import sys

# Ensure root path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app import create_app, db
from app.models import Contract, LiquidityPool

def create_test_contract():
    """Create a test Contract with all required fields."""
    return Contract(
        id=1,
        name="Test Contract",
        headline="Test headline for contract",
        original_headline="Original test headline",
        confidence=0.5
    )

def test_liquidity_pool_funding():
    app = create_app()
    with app.app_context():
        # Clean slate
        LiquidityPool.query.delete()
        Contract.query.delete()
        db.session.commit()

        # Create contract using helper
        contract = create_test_contract()
        db.session.add(contract)
        db.session.commit()

        # Create liquidity pool
        pool = LiquidityPool(
            contract_id=contract.id,
            max_liquidity=10000,
            current_liquidity=1000
        )
        db.session.add(pool)
        db.session.commit()

        # Fetch and validate
        fetched = LiquidityPool.query.filter_by(contract_id=contract.id).first()
        assert fetched is not None, "Test liquidity pool not found"
        assert fetched.max_liquidity == 10000, f"Expected max_liquidity 10000, got {fetched.max_liquidity}"
        assert fetched.current_liquidity == 1000, f"Expected current_liquidity 1000, got {fetched.current_liquidity}"

        print("✅ LiquidityPool test passed")

if __name__ == "__main__":
    test_liquidity_pool_funding()
