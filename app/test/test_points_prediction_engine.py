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
            user=self.user,
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

    def test_resolve_market_full_correct(self):
        """Test market resolution with all correct predictions"""
        # Create test users
        user1 = User(username="user1", email="user1@example.com")
        user2 = User(username="user2", email="user2@example.com")
        db.session.add_all([user1, user2])
        db.session.commit()

        # Create test market
        market = Market(
            title="Test Market",
            description="Test market for resolution",
            prediction_deadline=datetime.utcnow() + timedelta(days=1),
            resolution_deadline=datetime.utcnow() + timedelta(days=2),
            resolution_date=datetime.utcnow() + timedelta(days=3),
            resolution_method="Manual",
            yes_pool=1000.0,
            no_pool=1000.0,
            liquidity_pool=2000.0,
            liquidity_provider_shares=1.0,
            liquidity_fee=0.003
        )
        db.session.add(market)
        db.session.commit()

        # Create correct predictions
        prediction1 = Prediction(
            user=user1,
            market=market,
            shares=5.0,
            outcome=True
        )
        prediction2 = Prediction(
            user=user2,
            market=market,
            shares=3.0,
            outcome=True
        )
        db.session.add_all([prediction1, prediction2])
        db.session.commit()

        # Resolve market with correct outcome
        PointsPredictionEngine.resolve_market(market.id, True)

        # Verify results
        updated_market = Market.query.get(market.id)
        self.assertTrue(updated_market.resolved)
        self.assertEqual(updated_market.resolved_outcome, "YES")

        # Verify points and XP awarded
        updated_user1 = User.query.get(user1.id)
        updated_user2 = User.query.get(user2.id)
        self.assertEqual(updated_user1.points, 5)  # 5 shares
        self.assertEqual(updated_user1.xp, 5)
        self.assertEqual(updated_user2.points, 3)  # 3 shares
        self.assertEqual(updated_user2.xp, 3)

    def test_resolve_market_partial_correct(self):
        """Test market resolution with mixed predictions"""
        # Create test users
        user1 = User(username="user1", email="user1@example.com")
        user2 = User(username="user2", email="user2@example.com")
        db.session.add_all([user1, user2])
        db.session.commit()

        # Create test market
        market = Market(
            title="Test Market",
            description="Test market for resolution",
            prediction_deadline=datetime.utcnow() + timedelta(days=1),
            resolution_deadline=datetime.utcnow() + timedelta(days=2),
            resolution_date=datetime.utcnow() + timedelta(days=3),
            resolution_method="Manual",
            yes_pool=1000.0,
            no_pool=1000.0,
            liquidity_pool=2000.0,
            liquidity_provider_shares=1.0,
            liquidity_fee=0.003
        )
        db.session.add(market)
        db.session.commit()

        # Create predictions (one correct, one incorrect)
        prediction1 = Prediction(
            user=user1,
            market=market,
            shares=5.0,
            outcome=True  # Will be correct
        )
        prediction2 = Prediction(
            user=user2,
            market=market,
            shares=3.0,
            outcome=False  # Will be incorrect
        )
        db.session.add_all([prediction1, prediction2])
        db.session.commit()

        # Resolve market with correct outcome
        PointsPredictionEngine.resolve_market(market.id, True)

        # Verify results
        updated_market = Market.query.get(market.id)
        self.assertTrue(updated_market.resolved)
        self.assertEqual(updated_market.resolved_outcome, "YES")

        # Verify points and XP awarded
        updated_user1 = User.query.get(user1.id)
        updated_user2 = User.query.get(user2.id)
        self.assertEqual(updated_user1.points, 5)  # 5 shares
        self.assertEqual(updated_user1.xp, 5)
        self.assertEqual(updated_user2.points, 0)  # Incorrect prediction
        self.assertEqual(updated_user2.xp, 0)

    def test_resolve_market_all_incorrect(self):
        """Test market resolution with all incorrect predictions"""
        # Create test users
        user1 = User(username="user1", email="user1@example.com")
        user2 = User(username="user2", email="user2@example.com")
        db.session.add_all([user1, user2])
        db.session.commit()

        # Create test market
        market = Market(
            title="Test Market",
            description="Test market for resolution",
            prediction_deadline=datetime.utcnow() + timedelta(days=1),
            resolution_deadline=datetime.utcnow() + timedelta(days=2),
            resolution_date=datetime.utcnow() + timedelta(days=3),
            resolution_method="Manual",
            yes_pool=1000.0,
            no_pool=1000.0,
            liquidity_pool=2000.0,
            liquidity_provider_shares=1.0,
            liquidity_fee=0.003
        )
        db.session.add(market)
        db.session.commit()

        # Create incorrect predictions
        prediction1 = Prediction(
            user=user1,
            market=market,
            shares=5.0,
            outcome=False  # Will be incorrect
        )
        prediction2 = Prediction(
            user=user2,
            market=market,
            shares=3.0,
            outcome=False  # Will be incorrect
        )
        db.session.add_all([prediction1, prediction2])
        db.session.commit()

        # Resolve market with correct outcome
        PointsPredictionEngine.resolve_market(market.id, True)

        # Verify results
        updated_market = Market.query.get(market.id)
        self.assertTrue(updated_market.resolved)
        self.assertEqual(updated_market.resolved_outcome, "YES")

        # Verify no points or XP awarded
        updated_user1 = User.query.get(user1.id)
        updated_user2 = User.query.get(user2.id)
        self.assertEqual(updated_user1.points, 0)
        self.assertEqual(updated_user1.xp, 0)
        self.assertEqual(updated_user2.points, 0)
        self.assertEqual(updated_user2.xp, 0)

    def test_resolve_already_resolved_market(self):
        """Test resolving an already resolved market"""
        # Create test market
        market = Market(
            title="Test Market",
            description="Test market for resolution",
            prediction_deadline=datetime.utcnow() + timedelta(days=1),
            resolution_deadline=datetime.utcnow() + timedelta(days=2),
            resolution_date=datetime.utcnow() + timedelta(days=3),
            resolution_method="Manual",
            yes_pool=1000.0,
            no_pool=1000.0,
            liquidity_pool=2000.0,
            liquidity_provider_shares=1.0,
            liquidity_fee=0.003,
            resolved=True,
            resolved_outcome="YES"
        )
        db.session.add(market)
        db.session.commit()

        # Attempt to resolve again
        with self.assertRaises(ValueError):
            PointsPredictionEngine.resolve_market(market.id, True)

if __name__ == '__main__':
    unittest.main()
