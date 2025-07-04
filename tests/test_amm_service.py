import unittest
from app import create_app
from app.services.amm_service import AMMService
from app.models import db
from app.models.amm_market import AMMMarket
from app.models.liquidity_pool import LiquidityPool
from app.models.prediction import Prediction
from datetime import datetime, timedelta

class TestAMMService(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_calculate_share_allocation_balanced_market(self):
        """Test share allocation in a balanced market"""
        market_id = 1
        outcome = True
        amount = 100.0
        
        # Create test market and predictions
        market = AMMMarket(
            id=market_id,
            contract_id=market_id,  # Using market_id as contract_id for testing
            base_pool=1000.0,
            quote_pool=1000.0,
            total_shares_yes=0.0,
            total_shares_no=0.0
        )
        db.session.add(market)
        db.session.commit()
        
        result = AMMService.calculate_share_allocation(
            amount=amount,
            outcome=outcome,
            market_id=market_id
        )
        
        # Verify the allocation
        self.assertIn('shares', result)
        self.assertIn('price', result)
        self.assertIn('cost_before', result)
        self.assertIn('cost_after', result)
        self.assertGreater(result['shares'], 0)
        self.assertGreater(result['price'], 0)
        self.assertGreater(result['cost_before'], 0)
        self.assertGreater(result['cost_after'], result['cost_before'])
        
    def test_calculate_share_allocation_lopsided_market(self):
        """Test share allocation in a lopsided market"""
        market_id = 2
        outcome = False
        amount = 50.0
        
        # Create test market and predictions
        market = AMMMarket(
            id=market_id,
            contract_id=market_id,  # Using market_id as contract_id for testing
            base_pool=1000.0,
            quote_pool=500.0,
            total_shares_yes=0.0,
            total_shares_no=0.0
        )
        db.session.add(market)
        db.session.commit()
        
        result = AMMService.calculate_share_allocation(
            amount=amount,
            outcome=outcome,
            market_id=market_id
        )
        
        # Verify the allocation
        self.assertIn('shares', result)
        self.assertIn('price', result)
        self.assertIn('cost_before', result)
        self.assertIn('cost_after', result)
        self.assertGreater(result['shares'], 0)
        self.assertGreater(result['price'], 0)
        self.assertGreater(result['cost_before'], 0)
        self.assertGreater(result['cost_after'], result['cost_before'])

if __name__ == '__main__':
    unittest.main()
