import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from app import create_app
from app.models import User, Market, Prediction, db, PlatformWallet
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
        self.assertEqual(updated_user1.points, 5)  # 5 points
        self.assertEqual(updated_user1.xp, 5)
        self.assertEqual(updated_user2.points, 3)  # 3 points
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
        self.assertEqual(updated_user1.points, 5)  # 5 points
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

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_resolve_market_points_award(self, mock_log_transaction):
        """Test points awarding for correct predictions during market resolution"""
        # Create test users
        user1 = User(username="user1", email="user1@example.com")
        user2 = User(username="user2", email="user2@example.com")
        db.session.add_all([user1, user2])
        db.session.commit()

        # Create predictions
        pred1 = Prediction(
            user=user1,
            market=self.market,
            shares=10.0,
            outcome=True,
            xp_awarded=False
        )
        pred2 = Prediction(
            user=user2,
            market=self.market,
            shares=5.0,
            outcome=False,
            xp_awarded=False
        )
        db.session.add_all([pred1, pred2])
        db.session.commit()

        # Resolve market to YES (user1 should get points, user2 should not)
        PointsPredictionEngine.resolve_market(self.market.id, True)

        # Verify points were awarded correctly
        updated_user1 = User.query.get(user1.id)
        updated_user2 = User.query.get(user2.id)
        self.assertEqual(updated_user1.points, 10)  # 10 points
        self.assertEqual(updated_user1.xp, 10)     # 10 XP
        self.assertEqual(updated_user2.points, 0)   # No points for incorrect prediction
        self.assertEqual(updated_user2.xp, 0)       # No XP for incorrect prediction

        # Verify transaction logging
        self.assertEqual(mock_log_transaction.call_count, 2)
        mock_log_transaction.assert_any_call(
            user=user1,
            amount=10,
            transaction_type="points_awarded",
            description=f"Points awarded for correct prediction on market {self.market.id}"
        )
        mock_log_transaction.assert_any_call(
            user=user1,
            amount=0,
            transaction_type="xp_awarded",
            description=f"XP awarded for correct prediction on market {self.market.id}"
        )

    def test_points_award_only_once(self):
        """Test that points and XP are awarded only once"""
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

        # First resolution should award points and XP
        PointsPredictionEngine.resolve_market(self.market.id, True)
        updated_user = User.query.get(self.user.id)
        self.assertEqual(updated_user.points, 10)  # Points awarded
        self.assertEqual(updated_user.xp, 10)     # XP awarded

        # Second resolution should raise ValueError due to market already resolved
        with self.assertRaises(ValueError):
            PointsPredictionEngine.resolve_market(self.market.id, True)

        # Verify points and XP remain unchanged after error
        final_user = User.query.get(self.user.id)
        self.assertEqual(final_user.points, 10)  # Points remain unchanged
        self.assertEqual(final_user.xp, 10)      # XP remains unchanged

    def test_points_award_for_multiple_correct_predictions(self):
        """Test points awarding for multiple correct predictions"""
        # Create multiple users and predictions
        users = [User(username=f"user{i}", email=f"user{i}@example.com") for i in range(3)]
        db.session.add_all(users)
        db.session.commit()

        predictions = []
        total_points = 0
        for i, user in enumerate(users):
            shares = (i + 1) * 5  # 5, 10, 15 shares
            prediction = Prediction(
                user=user,
                market=self.market,
                shares=shares,
                outcome=True,
                xp_awarded=False
            )
            predictions.append(prediction)
            total_points += shares
            db.session.add(prediction)
        db.session.commit()

        # Resolve market to YES
        PointsPredictionEngine.resolve_market(self.market.id, True)

        # Verify points were awarded correctly
        for i, user in enumerate(users):
            updated_user = User.query.get(user.id)
            expected_points = (i + 1) * 5  # 5, 10, 15 points
            self.assertEqual(updated_user.points, expected_points)

        # Verify total points awarded
        total_awarded = sum(user.points for user in users)
        self.assertEqual(total_awarded, total_points)

    def test_place_prediction_with_fee(self):
        """Test prediction placement with platform fee deduction"""
        # Place prediction with 100 shares
        prediction = PointsPredictionEngine.place_prediction(
            self.user,
            self.market,
            shares=100.0,
            outcome=True
        )

        # Verify fee calculation (5% of 100 = 5)
        self.assertEqual(prediction.platform_fee, 5.0)
        
        # Verify net shares (100 - 5 = 95)
        self.assertEqual(prediction.shares, 100.0)  # Original amount stored

    def test_award_xp_with_fee(self):
        """Test XP awarding with platform fee deduction"""
        # Create prediction with 100 shares
        prediction = Prediction(
            user=self.user,
            market=self.market,
            shares=100.0,
            platform_fee=5.0,  # 5% fee
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

        # Verify XP was awarded based on gross shares (100)
        updated_prediction = Prediction.query.get(prediction.id)
        self.assertTrue(updated_prediction.xp_awarded)
        self.assertEqual(self.user.xp, 100)  # XP based on gross shares

    def test_resolve_market_with_fee(self):
        """Test market resolution with platform fee deduction"""
        # Create prediction with 100 shares
        prediction = Prediction(
            user=self.user,
            market=self.market,
            shares=100.0,
            platform_fee=5.0,  # 5% fee
            outcome=True,
            xp_awarded=False
        )
        db.session.add(prediction)
        db.session.commit()

        # Resolve market to YES
        PointsPredictionEngine.resolve_market(self.market.id, True)

        # Verify points and XP were awarded correctly
        updated_prediction = Prediction.query.get(prediction.id)
        self.assertTrue(updated_prediction.xp_awarded)
        self.assertEqual(self.user.points, 95)  # Points based on net shares (100 - 5)
        self.assertEqual(self.user.xp, 100)     # XP based on gross shares

    @patch('app.services.points_ledger.PointsLedger.log_transaction')
    def test_ledger_logging_with_fee(self, mock_log_transaction):
        """Test PointsLedger logging with platform fee deduction"""
        # Create prediction with 100 shares
        prediction = Prediction(
            user=self.user,
            market=self.market,
            shares=100.0,
            platform_fee=5.0,  # 5% fee
            outcome=True,
            xp_awarded=False
        )
        db.session.add(prediction)
        db.session.commit()

        # Resolve market to YES
        PointsPredictionEngine.resolve_market(self.market.id, True)

        # Verify transaction logging for points (based on net shares)
        mock_log_transaction.assert_any_call(
            user=self.user,
            amount=95,
            transaction_type="points_awarded",
            description=f"Points awarded for correct prediction on market {self.market.id}"
        )

        # Verify transaction logging for XP (based on gross shares)
        mock_log_transaction.assert_any_call(
            user=self.user,
            amount=0,
            transaction_type="xp_awarded",
            description=f"XP awarded for correct prediction on market {self.market.id}"
        )

    def test_fee_handling_with_none(self):
        """Test that platform fee handling works correctly when fee is None"""
        # Create prediction with no platform fee
        prediction = Prediction(
            user=self.user,
            market=self.market,
            shares=100.0,
            platform_fee=None,  # No fee
            outcome=True,
            xp_awarded=False
        )
        db.session.add(prediction)
        db.session.commit()

        # Resolve market to YES
        PointsPredictionEngine.resolve_market(self.market.id, True)

        # Verify points and XP were awarded correctly
        updated_prediction = Prediction.query.get(prediction.id)
        self.assertTrue(updated_prediction.xp_awarded)
        self.assertEqual(self.user.points, 100)  # Points based on gross shares (no fee)
        self.assertEqual(self.user.xp, 100)     # XP based on gross shares

    def test_award_xp_no_fee(self):
        """Test XP awarding when no platform fee exists"""
        # Create prediction with no platform fee
        prediction = Prediction(
            user=self.user,
            market=self.market,
            shares=100.0,
            platform_fee=None,  # No fee
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

        # Verify XP was awarded based on gross shares (100)
        updated_prediction = Prediction.query.get(prediction.id)
        self.assertTrue(updated_prediction.xp_awarded)
        self.assertEqual(self.user.xp, 100)  # XP based on gross shares

    def test_platform_wallet_initialization(self):
        """Test that PlatformWallet initializes with id=1 and balance=0.0"""
        # Reset wallet if exists
        wallet = PlatformWallet.query.get(1)
        if wallet:
            db.session.delete(wallet)
            db.session.commit()

        # Get wallet instance
        wallet = PlatformWallet.get_instance()
        
        # Verify initialization
        self.assertEqual(wallet.id, 1)
        self.assertEqual(wallet.balance, 0.0)

    def test_platform_wallet_accumulates_fee(self):
        """Test that PlatformWallet accumulates platform fees from predictions across multiple users"""
        # Reset wallet if exists
        wallet = PlatformWallet.query.get(1)
        if wallet:
            db.session.delete(wallet)
            db.session.commit()

        predictions = []
        expected_fees = []
        users = []

        # Create predictions with different users
        for i, shares in enumerate([100.0, 200.0, 150.0]):
            # Create a new user for each prediction
            user = User(
                username=f"fee_user_{i}",
                email=f"fee_user_{i}@example.com"
            )
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            users.append(user)

            # Place prediction
            prediction = PointsPredictionEngine.place_prediction(
                user,
                self.market,
                shares=shares,
                outcome=True
            )
            predictions.append(prediction)
            expected_fees.append(shares * 0.05)  # 5% fee

        # Verify each prediction has correct fee
        for prediction, expected_fee in zip(predictions, expected_fees):
            self.assertEqual(prediction.platform_fee, expected_fee)

        # Verify total fees in PlatformWallet
        wallet = PlatformWallet.query.get(1)
        total_expected = sum(expected_fees)
        self.assertIsNotNone(wallet)
        self.assertAlmostEqual(wallet.total_fees, total_expected, places=2)

        # Verify individual user fees
        for i, user in enumerate(users):
            user_predictions = Prediction.query.filter_by(user_id=user.id).all()
            self.assertEqual(len(user_predictions), 1)  # Each user should have exactly one prediction
            self.assertAlmostEqual(user_predictions[0].platform_fee, expected_fees[i], places=2)

    def test_platform_wallet_multiple_users(self):
        """Test that PlatformWallet correctly accumulates fees from multiple users"""
        # Reset wallet if exists
        wallet = PlatformWallet.query.get(1)
        if wallet:
            db.session.delete(wallet)
            db.session.commit()

        # Create two users
        user1 = User(username="user1", email="user1@example.com")
        user2 = User(username="user2", email="user2@example.com")
        user1.set_password("password")
        user2.set_password("password")
        db.session.add_all([user1, user2])
        db.session.commit()

        # User 1 makes predictions
        user1_predictions = []
        user1_expected = []
        for shares in [100.0, 150.0]:
            prediction = PointsPredictionEngine.place_prediction(
                user1,
                self.market,
                shares=shares,
                outcome=True
            )
            user1_predictions.append(prediction)
            user1_expected.append(shares * 0.05)

        # User 2 makes predictions
        user2_predictions = []
        user2_expected = []
        for shares in [200.0, 100.0]:
            prediction = PointsPredictionEngine.place_prediction(
                user2,
                self.market,
                shares=shares,
                outcome=True
            )
            user2_predictions.append(prediction)
            user2_expected.append(shares * 0.05)

        # Verify total fees
        wallet = PlatformWallet.query.get(1)
        total_expected = sum(user1_expected + user2_expected)
        self.assertAlmostEqual(wallet.total_fees, total_expected, places=2)

        # Verify individual user fees
        for pred, expected in zip(user1_predictions, user1_expected):
            self.assertAlmostEqual(pred.platform_fee, expected, places=2)
        for pred, expected in zip(user2_predictions, user2_expected):
            self.assertAlmostEqual(pred.platform_fee, expected, places=2)

    def test_platform_wallet_add_fee(self):
        """Test that add_fee method correctly accumulates fees"""
        # Reset wallet if exists
        wallet = PlatformWallet.query.get(1)
        if wallet:
            db.session.delete(wallet)
            db.session.commit()

        # Get fresh wallet instance
        wallet = PlatformWallet.get_instance()
        
        # Add multiple fees
        fees = [10.0, 20.0, 15.0]
        for fee in fees:
            wallet.add_fee(fee)

        # Verify total balance
        expected_balance = sum(fees)
        self.assertEqual(wallet.balance, expected_balance)

    def test_platform_wallet_singleton(self):
        """Test that PlatformWallet is a singleton (always returns same instance)"""
        # Reset wallet if exists
        wallet = PlatformWallet.query.get(1)
        if wallet:
            db.session.delete(wallet)
            db.session.commit()

        # Get two instances
        wallet1 = PlatformWallet.get_instance()
        wallet2 = PlatformWallet.get_instance()

        # Verify they are the same instance
        self.assertEqual(wallet1.id, 1)
        self.assertEqual(wallet2.id, 1)
        self.assertEqual(wallet1, wallet2)

        # Add fee through one instance
        wallet1.add_fee(10.0)

        # Verify balance is updated in both instances
        self.assertEqual(wallet1.balance, 10.0)
        self.assertEqual(wallet2.balance, 10.0)

    def test_liquidity_buffer_majority_correct(self):
        """Test liquidity buffer simulation where majority predictions are correct"""
        # Reset wallet and LB
        wallet = PlatformWallet.query.get(1)
        if wallet:
            db.session.delete(wallet)
            db.session.commit()

        # Create market
        market = Market(
            title="Test Market",
            description="Test market for liquidity buffer simulation",
            prediction_deadline=datetime.utcnow() + timedelta(days=1),
            resolution_deadline=datetime.utcnow() + timedelta(days=2),
            resolution_date=datetime.utcnow() + timedelta(days=2),
            resolution_method="Manual",
            created_at=datetime.utcnow()
        )
        db.session.add(market)
        db.session.commit()

        # Create 3 users with liquidity buffer
        users = []
        for i in range(3):
            user = User(
                username=f"user_{i}",
                email=f"user_{i}@example.com",
                liquidity_buffer_deposit=1000.0  # Each user starts with 1000 LB
            )
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            users.append(user)

        # User 1 and 2 predict YES (majority)
        for user in users[:2]:
            prediction = PointsPredictionEngine.place_prediction(
                user,
                market,
                shares=500.0,
                outcome=True,
                use_liquidity_buffer=True
            )
            self.assertTrue(prediction.used_liquidity_buffer)
            self.assertEqual(user.liquidity_buffer_deposit, 500.0)  # 500 used

        # User 3 predicts NO (minority)
        prediction = PointsPredictionEngine.place_prediction(
            users[2],
            market,
            shares=500.0,
            outcome=False,
            use_liquidity_buffer=True
        )
        self.assertTrue(prediction.used_liquidity_buffer)
        self.assertEqual(users[2].liquidity_buffer_deposit, 500.0)  # 500 used

        # Resolve market to YES (majority correct)
        PointsPredictionEngine.resolve_market(market.id, True)

        # Verify platform wallet received fees
        wallet = PlatformWallet.query.get(1)
        self.assertEqual(wallet.total_fees, 75.0)  # 5% of 1500 total shares

        # Verify users' liquidity buffer deposits remain stable
        for user in users:
            self.assertEqual(user.liquidity_buffer_deposit, 500.0)  # No refund to LB

        # Verify majority users (1 and 2) received correct points
        for user in users[:2]:
            # Each gets 475 points (500 - 5% fee)
            self.assertEqual(user.points, 475)
            self.assertEqual(user.xp, 500)  # Gross shares

        # Verify minority user (3) lost stake and got no points
        self.assertEqual(users[2].points, 0)
        self.assertEqual(users[2].xp, 0)  # Incorrect prediction

        # Verify no double payouts
        for user in users:
            if user.predictions[0].outcome == True:  # Only correct predictions should have xp_awarded
                self.assertTrue(user.predictions[0].xp_awarded)
            else:
                self.assertFalse(user.predictions[0].xp_awarded)

    def test_liquidity_buffer_majority_incorrect(self):
        """Test liquidity buffer simulation where majority predictions are incorrect"""
        # Reset wallet and LB
        wallet = PlatformWallet.query.get(1)
        if wallet:
            db.session.delete(wallet)
            db.session.commit()

        # Create market
        market = Market(
            title="Test Market",
            description="Test market for liquidity buffer simulation",
            prediction_deadline=datetime.utcnow() + timedelta(days=1),
            resolution_deadline=datetime.utcnow() + timedelta(days=2),
            resolution_date=datetime.utcnow() + timedelta(days=2),
            resolution_method="Manual",
            created_at=datetime.utcnow()
        )
        db.session.add(market)
        db.session.commit()

        # Create 3 users with liquidity buffer
        users = []
        for i in range(3):
            user = User(
                username=f"user_{i}",
                email=f"user_{i}@example.com",
                liquidity_buffer_deposit=1000.0  # Each user starts with 1000 LB
            )
            user.set_password("password")
            db.session.add(user)
            db.session.commit()
            users.append(user)

        # User 1 and 2 predict YES (majority)
        for user in users[:2]:
            prediction = PointsPredictionEngine.place_prediction(
                user,
                market,
                shares=500.0,
                outcome=True,
                use_liquidity_buffer=True
            )
            self.assertTrue(prediction.used_liquidity_buffer)
            self.assertEqual(user.liquidity_buffer_deposit, 500.0)  # 500 used

        # User 3 predicts NO (minority)
        prediction = PointsPredictionEngine.place_prediction(
            users[2],
            market,
            shares=500.0,
            outcome=False,
            use_liquidity_buffer=True
        )
        self.assertTrue(prediction.used_liquidity_buffer)
        self.assertEqual(users[2].liquidity_buffer_deposit, 500.0)  # 500 used

        # Resolve market to NO (minority correct)
        PointsPredictionEngine.resolve_market(market.id, False)

        # Verify platform wallet received fees
        wallet = PlatformWallet.query.get(1)
        self.assertEqual(wallet.total_fees, 75.0)  # 5% of 1500 total shares

        # Verify users' liquidity buffer deposits remain stable
        for user in users:
            self.assertEqual(user.liquidity_buffer_deposit, 500.0)  # No refund to LB

        # Verify majority users (1 and 2) lost stake and got no points
        for user in users[:2]:
            self.assertEqual(user.points, 0)
            self.assertEqual(user.xp, 0)  # Incorrect prediction

        # Verify minority user (3) received correct points
        # Note: Points are based on their own shares (500 - 5% fee), not total pool
        self.assertEqual(users[2].points, 475)  # 500 - 5% fee
        self.assertEqual(users[2].xp, 500)  # Gross shares

        # Verify no double payouts
        for user in users:
            if user.predictions[0].outcome == False:  # Only correct predictions should have xp_awarded
                self.assertTrue(user.predictions[0].xp_awarded)
            else:
                self.assertFalse(user.predictions[0].xp_awarded)

if __name__ == '__main__':
    unittest.main()
