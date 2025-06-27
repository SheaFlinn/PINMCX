import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from app import create_app
from app.models import User, Market, Prediction, db
from app.services.points_prediction_engine import PointsPredictionEngine

class PointsPredictionEngineTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test user
        self.user = User(username="test_user", email="test@example.com")
        db.session.add(self.user)
        db.session.commit()
        
        # Create test market
        self.market = Market(
            title="Test Market",
            description="Test market for predictions",
            prediction_deadline=datetime.utcnow() + timedelta(days=1),
            resolution_deadline=datetime.utcnow() + timedelta(days=2),
            resolution_date=datetime.utcnow() + timedelta(days=3),
            resolution_method="Manual",
            yes_pool=1000.0,
            no_pool=1000.0,
            liquidity_pool=2000.0,
            liquidity_provider_shares=1.0,
            liquidity_fee=0.003,
            created_at=datetime.utcnow()
        )
        db.session.add(self.market)
        db.session.commit()

    def tearDown(self):
        """Tear down test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_place_prediction(self):
        """Test placing a valid prediction"""
        prediction = PointsPredictionEngine.place_prediction(
            self.user,
            self.market,
            shares=10.0,
            outcome=True
        )
        self.assertIsNotNone(prediction.id)
        self.assertEqual(prediction.user_id, self.user.id)
        self.assertEqual(prediction.market_id, self.market.id)
        self.assertEqual(prediction.shares, 10.0)
        self.assertTrue(prediction.outcome)

    def test_place_prediction_after_deadline(self):
        """Test placing prediction after deadline"""
        # Set market deadline to past
        self.market.prediction_deadline = datetime.utcnow() - timedelta(days=1)
        db.session.commit()

        with self.assertRaises(ValueError):
            PointsPredictionEngine.place_prediction(
                self.user,
                self.market,
                shares=10.0,
                outcome=True
            )

    def test_place_duplicate_prediction(self):
        """Test placing duplicate prediction"""
        # Place first prediction
        PointsPredictionEngine.place_prediction(
            self.user,
            self.market,
            shares=10.0,
            outcome=True
        )

        # Attempt to place second prediction
        with self.assertRaises(ValueError):
            PointsPredictionEngine.place_prediction(
                self.user,
                self.market,
                shares=10.0,
                outcome=True
            )

    def test_evaluate_prediction_correct(self):
        """Test evaluating correct prediction"""
        # Create prediction
        prediction = Prediction(
            user=self.user,
            market=self.market,
            shares=10.0,
            outcome=True
        )
        db.session.add(prediction)
        db.session.commit()

        # Set market to resolve YES
        self.market.resolved = True
        self.market.resolved_outcome = "YES"
        self.market.resolved_at = datetime.utcnow()
        db.session.commit()

        result = PointsPredictionEngine.evaluate_prediction(prediction, self.market)
        self.assertTrue(result)

    def test_evaluate_prediction_incorrect(self):
        """Test evaluating incorrect prediction"""
        # Create prediction
        prediction = Prediction(
            user=self.user,
            market=self.market,
            shares=10.0,
            outcome=False
        )
        db.session.add(prediction)
        db.session.commit()

        # Set market to resolve YES
        self.market.resolved = True
        self.market.resolved_outcome = "YES"
        self.market.resolved_at = datetime.utcnow()
        db.session.commit()

        result = PointsPredictionEngine.evaluate_prediction(prediction, self.market)
        self.assertFalse(result)

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_award_xp_for_predictions(self, mock_log_transaction):
        """Test XP awarding for correct predictions"""
        # Create prediction
        prediction = Prediction(
            user=self.user,
            market=self.market,
            shares=10.0,
            outcome=True,
            xp_awarded=False
        )
        db.session.add(prediction)
        db.session.commit()

        # Set market to resolve YES
        self.market.resolved = True
        self.market.resolved_outcome = "YES"
        self.market.resolved_at = datetime.utcnow()
        db.session.commit()

        # Award XP
        PointsPredictionEngine.award_xp_for_predictions(self.market)

        # Verify XP was awarded
        updated_prediction = Prediction.query.get(prediction.id)
        self.assertTrue(updated_prediction.xp_awarded)
        self.assertEqual(self.user.xp, 10)  # 1 XP per share

        # Verify ledger logging
        mock_log_transaction.assert_called_once_with(
            user_id=self.user.id,
            amount=0,
            transaction_type="xp_awarded",
            description=f"XP awarded for correct prediction on market {self.market.id}"
        )

    def test_award_xp_no_double_award(self):
        """Test that XP isn't awarded twice"""
        # Create prediction
        prediction = Prediction(
            user=self.user,
            market=self.market,
            shares=10.0,
            outcome=True,
            xp_awarded=True  # Already awarded
        )
        db.session.add(prediction)
        db.session.commit()

        # Set market to resolve YES
        self.market.resolved = True
        self.market.resolved_outcome = "YES"
        self.market.resolved_at = datetime.utcnow()
        db.session.commit()

        # Award XP (should be skipped)
        PointsPredictionEngine.award_xp_for_predictions(self.market)

        # Verify XP wasn't awarded again
        updated_prediction = Prediction.query.get(prediction.id)
        self.assertEqual(self.user.xp, 0)  # Should remain unchanged

if __name__ == '__main__':
    unittest.main()
