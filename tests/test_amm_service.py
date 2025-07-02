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
    def test_get_current_odds_balanced(self, balanced_pool):
        """Test odds calculation from a balanced pool"""
        odds = AMMService.get_current_odds(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity,
            current_odds_yes=balanced_pool.current_odds_yes,
            current_odds_no=balanced_pool.current_odds_no
        )
        assert odds['yes'] == pytest.approx(0.5)
        assert odds['no'] == pytest.approx(0.5)

    def test_share_allocation_small_stake_yes(self, balanced_pool):
        """Test YES-side share allocation for small stake"""
        initial_k = balanced_pool.yes_liquidity * balanced_pool.no_liquidity
        
        # Calculate allocation
        result = AMMService.calculate_share_allocation(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity,
            stake=10.0,
            outcome="YES"
        )
        
        # Verify AMM invariance
        final_k = result['yes_liquidity'] * result['no_liquidity']
        assert final_k == pytest.approx(initial_k)
        
        # Verify liquidity changes
        assert result['yes_liquidity'] == pytest.approx(110.0)
        assert result['no_liquidity'] == pytest.approx(90.90909090909091)

    def test_share_allocation_large_stake_no(self, balanced_pool):
        """Test NO-side share allocation for large stake"""
        initial_k = balanced_pool.yes_liquidity * balanced_pool.no_liquidity
        
        # Calculate allocation
        result = AMMService.calculate_share_allocation(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity,
            stake=500.0,
            outcome="NO"
        )
        
        # Verify AMM invariance
        final_k = result['yes_liquidity'] * result['no_liquidity']
        assert final_k == pytest.approx(initial_k)
        
        # Verify liquidity changes
        assert result['no_liquidity'] == pytest.approx(600.0)
        assert result['yes_liquidity'] == pytest.approx(16.666666666666668)

    def test_constant_product_invariance(self, balanced_pool):
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
                outcome="YES"
            )
            yes_liquidity = result['yes_liquidity']
            no_liquidity = result['no_liquidity']
        
        # Verify k remains constant
        final_k = yes_liquidity * no_liquidity
        assert final_k == pytest.approx(initial_k)

    def test_odds_update_accuracy(self, balanced_pool):
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
            outcome="YES"
        )
        
        # Update and verify new odds
        odds = AMMService.get_current_odds(
            yes_liquidity=result['yes_liquidity'],
            no_liquidity=result['no_liquidity']
        )
        assert odds['yes'] == pytest.approx(0.2)
        assert odds['no'] == pytest.approx(0.8)

    def test_zero_liquidity_error(self, empty_pool):
        """Test error handling for zero liquidity"""
        with pytest.raises(ZeroDivisionError):
            AMMService.get_current_odds(
                yes_liquidity=empty_pool.yes_liquidity,
                no_liquidity=empty_pool.no_liquidity,
                current_odds_yes=empty_pool.current_odds_yes,
                current_odds_no=empty_pool.current_odds_no
            )

    def test_tiny_liquidity(self, tiny_pool):
        """Test behavior with very small liquidity amounts"""
        initial_k = tiny_pool.yes_liquidity * tiny_pool.no_liquidity
        
        # Calculate allocation
        result = AMMService.calculate_share_allocation(
            yes_liquidity=tiny_pool.yes_liquidity,
            no_liquidity=tiny_pool.no_liquidity,
            stake=1e-7,
            outcome="YES"
        )
        
        # Verify AMM invariance
        final_k = result['yes_liquidity'] * result['no_liquidity']
        assert final_k == pytest.approx(initial_k)
        
        # Verify liquidity changes
        # After adding 1e-7 to YES side:
        # new_yes_liquidity = 1e-6 + 1e-7 = 1.1e-6
        # new_no_liquidity = 1e-12 / 1.1e-6 = 9.090909090909091e-7
        assert result['yes_liquidity'] == pytest.approx(1.1e-6)
        assert result['no_liquidity'] == pytest.approx(9.090909090909091e-7)

    def test_large_stake_impact(self, balanced_pool):
        """Test impact of very large stake on pool"""
        initial_k = balanced_pool.yes_liquidity * balanced_pool.no_liquidity
        
        # Calculate allocation
        result = AMMService.calculate_share_allocation(
            yes_liquidity=balanced_pool.yes_liquidity,
            no_liquidity=balanced_pool.no_liquidity,
            stake=10000.0,
            outcome="YES"
        )
        
        # Verify AMM invariance
        final_k = result['yes_liquidity'] * result['no_liquidity']
        assert final_k == pytest.approx(initial_k)
        
        # Verify liquidity changes
        assert result['yes_liquidity'] == pytest.approx(10100.0)
        assert result['no_liquidity'] == pytest.approx(0.9900990099009901)

import unittest
from app.services.amm_service import AMMService

class TestAMMService(unittest.TestCase):
    def test_get_current_odds(self):
        # Test with equal liquidity
        result = AMMService.get_current_odds(100, 100)
        self.assertEqual(result['yes'], 0.5)
        self.assertEqual(result['no'], 0.5)
        
        # Test with unequal liquidity
        result = AMMService.get_current_odds(100, 200)
        self.assertEqual(result['yes'], 0.6666666666666666)
        self.assertEqual(result['no'], 0.3333333333333333)
        
        # Test zero liquidity
        with self.assertRaises(ZeroDivisionError):
            AMMService.get_current_odds(0, 0)

    def test_calculate_share_allocation_yes(self):
        # Test YES allocation with small stake
        result = AMMService.calculate_share_allocation(100, 100, 10, "YES")
        self.assertAlmostEqual(result['yes_liquidity'], 110)
        self.assertAlmostEqual(result['no_liquidity'], 90.90909090909091)
        self.assertAlmostEqual(result['shares_purchased'], 9.09090909090909)
        self.assertGreater(result['slippage'], 0)
        
        # Test YES allocation with large stake
        result = AMMService.calculate_share_allocation(100, 100, 100, "YES")
        self.assertAlmostEqual(result['yes_liquidity'], 200)
        self.assertAlmostEqual(result['no_liquidity'], 50)
        self.assertAlmostEqual(result['shares_purchased'], 50)
        self.assertGreater(result['slippage'], 0)

    def test_calculate_share_allocation_no(self):
        # Test NO allocation with small stake
        result = AMMService.calculate_share_allocation(100, 100, 10, "NO")
        self.assertAlmostEqual(result['yes_liquidity'], 90.90909090909091)
        self.assertAlmostEqual(result['no_liquidity'], 110)
        self.assertAlmostEqual(result['shares_purchased'], 9.09090909090909)
        self.assertGreater(result['slippage'], 0)
        
        # Test NO allocation with large stake
        result = AMMService.calculate_share_allocation(100, 100, 100, "NO")
        self.assertAlmostEqual(result['yes_liquidity'], 50)
        self.assertAlmostEqual(result['no_liquidity'], 200)
        self.assertAlmostEqual(result['shares_purchased'], 50)
        self.assertGreater(result['slippage'], 0)

    def test_invalid_outcome(self):
        with self.assertRaises(ValueError):
            AMMService.calculate_share_allocation(100, 100, 10, "INVALID")

    def test_negative_liquidity(self):
        with self.assertRaises(ZeroDivisionError):
            AMMService.calculate_share_allocation(-100, 100, 10, "YES")
        
        with self.assertRaises(ZeroDivisionError):
            AMMService.calculate_share_allocation(100, -100, 10, "YES")

if __name__ == '__main__':
    unittest.main()
