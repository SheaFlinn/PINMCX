import pytest
from unittest.mock import MagicMock
from app.services.amm_service import AMMService

class MockLiquidityPool:
    def __init__(self):
        self.yes_liquidity = 0.0
        self.no_liquidity = 0.0
        self.current_odds_yes = 0.5
        self.current_odds_no = 0.5

# Test fixture for a basic 50/50 pool
@pytest.fixture
def balanced_pool():
    pool = MockLiquidityPool()
    pool.yes_liquidity = 100.0
    pool.no_liquidity = 100.0
    return pool

# Test fixture for a pool with zero liquidity
@pytest.fixture
def empty_pool():
    pool = MockLiquidityPool()
    pool.yes_liquidity = 0.0
    pool.no_liquidity = 0.0
    return pool

# Test fixture for a pool with very small liquidity
@pytest.fixture
def tiny_pool():
    pool = MockLiquidityPool()
    pool.yes_liquidity = 1e-6
    pool.no_liquidity = 1e-6
    return pool

class TestAMMCore:
    def legacy_test_get_current_odds_balanced(self, balanced_pool):
        """Test odds calculation from a balanced pool"""
        odds = AMMService.get_current_odds(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity
        )
        assert odds['yes'] == pytest.approx(0.5)
        assert odds['no'] == pytest.approx(0.5)

    def legacy_test_share_allocation_small_stake_yes(self, balanced_pool):
        """Test YES-side share allocation for small stake"""
        initial_k = balanced_pool.yes_liquidity * balanced_pool.no_liquidity
        
        # Calculate allocation
        result = AMMService.calculate_share_allocation(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity,
            stake=10.0,
            outcome=True
        )
        
        # Verify AMM invariance
        final_k = result['yes_liquidity'] * result['no_liquidity']
        assert final_k == pytest.approx(initial_k)
        
        # Verify liquidity changes
        assert result['yes_liquidity'] == pytest.approx(110.0)
        assert result['no_liquidity'] == pytest.approx(90.90909090909091)

    def legacy_test_share_allocation_large_stake_no(self, balanced_pool):
        """Test NO-side share allocation for large stake"""
        initial_k = balanced_pool.yes_liquidity * balanced_pool.no_liquidity
        
        # Calculate allocation
        result = AMMService.calculate_share_allocation(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity,
            stake=500.0,
            outcome=False
        )
        
        # Verify AMM invariance
        final_k = result['yes_liquidity'] * result['no_liquidity']
        assert final_k == pytest.approx(initial_k)
        
        # Verify liquidity changes
        assert result['no_liquidity'] == pytest.approx(600.0)
        assert result['yes_liquidity'] == pytest.approx(16.666666666666668)

    def legacy_test_constant_product_invariance(self, balanced_pool):
        """Test AMM constant product formula invariance"""
        initial_k = balanced_pool.yes_liquidity * balanced_pool.no_liquidity
        
        # Make multiple trades
        yes_liquidity = balanced_pool.yes_liquidity
        no_liquidity = balanced_pool.no_liquidity
        
        for stake in [10.0, 20.0, 30.0]:
            result = AMMService.calculate_share_allocation(
                yes_liquidity=yes_liquidity,
                no_liquidity=no_liquidity,
                stake=stake,
                outcome=True
            )
            yes_liquidity = result['yes_liquidity']
            no_liquidity = result['no_liquidity']
        
        # Verify k remains constant
        final_k = yes_liquidity * no_liquidity
        assert final_k == pytest.approx(initial_k)

    def legacy_test_zero_liquidity_error(self, empty_pool):
        """Test error handling for zero liquidity"""
        with pytest.raises(ZeroDivisionError):
            AMMService.get_current_odds(
                yes_liquidity=empty_pool.yes_liquidity,
                no_liquidity=empty_pool.no_liquidity
            )

    def legacy_test_odds_update_accuracy(self, balanced_pool):
        """Test accuracy of odds updates after trades"""
        # Initial odds should be 0.5
        odds = AMMService.get_current_odds(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity
        )
        assert odds['yes'] == pytest.approx(0.5)
        assert odds['no'] == pytest.approx(0.5)
        
        # Make a trade
        result = AMMService.calculate_share_allocation(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity,
            stake=100.0,
            outcome=True
        )
        
        # Update and verify new odds
        odds = AMMService.get_current_odds(
            yes_liquidity=result['yes_liquidity'],
            no_liquidity=result['no_liquidity']
        )
        assert odds['yes'] == pytest.approx(0.2)
        assert odds['no'] == pytest.approx(0.8)

    def legacy_test_update_odds(self, balanced_pool):
        """Test update_odds method"""
        pool = MockLiquidityPool()
        pool.yes_liquidity = balanced_pool.yes_liquidity
        pool.no_liquidity = balanced_pool.no_liquidity
        
        # Initial odds should be 0.5
        AMMService.update_odds(pool)
        assert pool.current_odds_yes == pytest.approx(0.5)
        assert pool.current_odds_no == pytest.approx(0.5)
        
        # Make a trade
        result = AMMService.calculate_share_allocation(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity,
            stake=100.0,
            outcome=True
        )
        
        # Update pool liquidity
        pool.yes_liquidity = result['yes_liquidity']
        pool.no_liquidity = result['no_liquidity']
        
        # Update and verify new odds
        AMMService.update_odds(pool)
        assert pool.current_odds_yes == pytest.approx(0.2)
        assert pool.current_odds_no == pytest.approx(0.8)

    def legacy_test_tiny_liquidity(self, tiny_pool):
        """Test behavior with very small liquidity amounts"""
        initial_k = tiny_pool.yes_liquidity * tiny_pool.no_liquidity
        
        # Calculate allocation
        result = AMMService.calculate_share_allocation(
            yes_liquidity=tiny_pool.yes_liquidity,
            no_liquidity=tiny_pool.no_liquidity,
            stake=1e-7,
            outcome=True
        )
        
        # Verify AMM invariance
        final_k = result['yes_liquidity'] * result['no_liquidity']
        assert final_k == pytest.approx(initial_k)
        
        # Verify liquidity changes
        assert result['yes_liquidity'] == pytest.approx(1.1e-6)
        assert result['no_liquidity'] == pytest.approx(9.090909090909091e-7)

    def legacy_test_large_stake_impact(self, balanced_pool):
        """Test impact of very large stake on pool"""
        initial_k = balanced_pool.yes_liquidity * balanced_pool.no_liquidity
        
        # Calculate allocation
        result = AMMService.calculate_share_allocation(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity,
            stake=10000.0,
            outcome=True
        )
        
        # Verify AMM invariance
        final_k = result['yes_liquidity'] * result['no_liquidity']
        assert final_k == pytest.approx(initial_k)
        
        # Verify liquidity changes
        assert result['yes_liquidity'] == pytest.approx(10100.0)
        assert result['no_liquidity'] == pytest.approx(9.900990099009901)
