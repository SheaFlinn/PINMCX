import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from app import create_app, db
from app.models import User, Market, Prediction, PlatformWallet
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
            deadline=datetime.utcnow() + timedelta(days=3),
            creator_id=self.user.id,
            platform_fee=0.05,
            liquidity_fee=0.003,
            status='open'
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
        self.assertEqual(prediction.stake, 10.0)
        self.assertEqual(prediction.outcome, 'YES')
        self.assertEqual(prediction.confidence, 9.5)  # 10.0 - 5% fee
        self.assertIsNotNone(prediction.timestamp)

    def test_place_prediction_after_deadline(self):
        """Test placing prediction after deadline"""
        # Set market deadline to past
        self.market.deadline = datetime.utcnow() - timedelta(days=1)
        db.session.commit()

        with self.assertRaises(ValueError):
            PointsPredictionEngine.place_prediction(
                self.user,
                self.market,
                shares=10.0,
                outcome=True
            )

    def test_place_multiple_predictions(self):
        """Test placing multiple predictions from same user on same market"""
        # Place first prediction
        prediction1 = PointsPredictionEngine.place_prediction(
            self.user,
            self.market,
            shares=10.0,
            outcome=True
        )
        self.assertIsNotNone(prediction1.id)
        self.assertEqual(prediction1.stake, 10.0)
        self.assertEqual(prediction1.confidence, 9.5)  # 10.0 - 5% fee

        # Place second prediction
        prediction2 = PointsPredictionEngine.place_prediction(
            self.user,
            self.market,
            shares=15.0,
            outcome=False
        )
        self.assertIsNotNone(prediction2.id)
        self.assertNotEqual(prediction1.id, prediction2.id)
        self.assertEqual(prediction2.stake, 15.0)
        self.assertEqual(prediction2.confidence, 14.25)  # 15.0 - 5% fee

        # Verify both predictions exist
        predictions = Prediction.query.filter_by(
            user_id=self.user.id,
            market_id=self.market.id
        ).all()
        self.assertEqual(len(predictions), 2)

    def test_evaluate_prediction_correct(self):
        """Test evaluating correct prediction"""
        # Create a prediction
        prediction = PointsPredictionEngine.place_prediction(
            self.user,
            self.market,
            shares=10.0,
            outcome=True
        )
        
        # Resolve market correctly
        self.market.resolve('YES')
        
        # Evaluate prediction
        is_correct = PointsPredictionEngine.evaluate_prediction(prediction, self.market)
        self.assertTrue(is_correct)

    def test_evaluate_prediction_incorrect(self):
        """Test evaluating incorrect prediction"""
        # Create a prediction
        prediction = PointsPredictionEngine.place_prediction(
            self.user,
            self.market,
            shares=10.0,
            outcome=False
        )
        
        # Resolve market incorrectly
        self.market.resolve('YES')
        
        # Evaluate prediction
        is_correct = PointsPredictionEngine.evaluate_prediction(prediction, self.market)
        self.assertFalse(is_correct)

    def test_award_xp_for_prediction(self):
        """Test XP award for correct prediction"""
        # Create a prediction
        prediction = PointsPredictionEngine.place_prediction(
            self.user,
            self.market,
            shares=10.0,
            outcome=True
        )
        
        # Resolve market correctly
        self.market.resolve('YES')
        
        # Award XP
        PointsPredictionEngine.award_xp_for_prediction(prediction)
        
        # Verify XP was awarded
        self.assertGreater(self.user.xp, 0)

    def test_award_points_for_prediction(self):
        """Test points award for correct prediction"""
        # Create a prediction
        prediction = PointsPredictionEngine.place_prediction(
            self.user,
            self.market,
            shares=10.0,
            outcome=True
        )
        
        # Resolve market correctly
        self.market.resolve('YES')
        
        # Award points
        PointsPredictionEngine.award_points_for_prediction(prediction)
        
        # Verify points were awarded
        self.assertGreater(self.user.points, 0)

    def test_platform_fee_accumulation(self):
        """Test platform fee accumulation"""
        # Create a prediction
        prediction = PointsPredictionEngine.place_prediction(
            self.user,
            self.market,
            shares=10.0,
            outcome=True
        )
        
        # Resolve market correctly
        self.market.resolve('YES')
        
        # Award points (should trigger fee collection)
        PointsPredictionEngine.award_points_for_prediction(prediction)
        
        # Verify platform fee was collected
        platform_wallet = PlatformWallet.get_instance()
        self.assertGreater(platform_wallet.total_fees, 0)

if __name__ == '__main__':
    unittest.main()
