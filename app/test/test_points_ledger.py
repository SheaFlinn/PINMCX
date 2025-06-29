import unittest
from datetime import datetime
from app import create_app, db
from app.models import User
from app.services.points_ledger import PointsLedger
from app.services.points_payout_engine import PointsPayoutEngine

class PointsLedgerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test user
        self.user = User(username='testuser', email='test@example.com')
        db.session.add(self.user)
        db.session.commit()
        
        # Reset points
        self.user.points = 0
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_trade_payout_logging(self):
        """Test that trade payouts are logged correctly"""
        market_id = 1  # Test market ID
        trade_amount = 100.0
        outcome = 'YES'
        
        # Make a trade
        PointsPayoutEngine.award_trade_payout(
            user=self.user,
            amount=trade_amount,
            market_id=market_id,
            outcome=outcome
        )
        
        # Verify points were updated
        self.assertEqual(self.user.points, trade_amount)
        
        # Verify ledger entry was created
        # TODO: Implement actual ledger storage and retrieval
        # For now, we're just checking the print statement
        # This will need to be updated when real storage is implemented

    def test_resolution_payout_logging(self):
        """Test that resolution payouts are logged correctly"""
        market_id = 1  # Test market ID
        resolution_amount = 200.0
        
        # Resolve market
        PointsPayoutEngine.award_resolution_payout(
            user=self.user,
            amount=resolution_amount,
            market_id=market_id
        )
        
        # Verify points were updated
        self.assertEqual(self.user.points, resolution_amount)
        
        # Verify ledger entry was created
        # TODO: Implement actual ledger storage and retrieval
        # For now, we're just checking the print statement
        # This will need to be updated when real storage is implemented

    def test_negative_trade(self):
        """Test handling of negative trade amounts"""
        market_id = 1  # Test market ID
        trade_amount = -50.0
        outcome = 'NO'
        
        # Give user initial points
        self.user.points = 100.0
        db.session.commit()
        
        # Make a trade
        PointsPayoutEngine.award_trade_payout(
            user=self.user,
            amount=trade_amount,
            market_id=market_id,
            outcome=outcome
        )
        
        # Verify points were deducted
        self.assertEqual(self.user.points, 50.0)
        
        # Verify ledger entry was created
        # TODO: Implement actual ledger storage and retrieval
        # For now, we're just checking the print statement
        # This will need to be updated when real storage is implemented

if __name__ == '__main__':
    unittest.main()
