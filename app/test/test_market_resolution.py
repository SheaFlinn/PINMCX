import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Market, Prediction, Badge

class TestMarketResolution(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Ensure all models are imported before creating tables
        User  # Force import of User model
        Market  # Force import of Market model
        Prediction  # Force import of Prediction model
        Badge  # Force import of Badge model

        # Create test users
        self.user1 = User(username='test1', email='test1@example.com')
        self.user2 = User(username='test2', email='test2@example.com')
        db.session.add_all([self.user1, self.user2])
        db.session.commit()

        # Create test market
        self.market = Market(
            title="Will it rain tomorrow?",
            description="A test market for rain prediction",
            resolution_date=datetime.utcnow() + timedelta(days=1),
            resolution_method="manual",
            domain="weather",
            yes_pool=1000.0,
            no_pool=1000.0,
            liquidity_pool=2000.0,
            liquidity_provider_shares=1.0,
            liquidity_fee=0.003
        )
        db.session.add(self.market)
        db.session.commit()

        # Create test prediction
        self.prediction = Prediction(
            user_id=self.user1.id,
            market_id=self.market.id,
            outcome=True,
            shares=10
        )
        db.session.add(self.prediction)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_sanity(self):
        """Ensure user and market tables exist and one user + one market exist."""
        user_count = User.query.count()
        market_count = Market.query.count()
        self.assertEqual(user_count, 2)
        self.assertEqual(market_count, 1)

    def test_correct_prediction_awards_xp(self):
        """Test that correct predictions award XP"""
        # Make a correct prediction
        self.prediction.outcome = True
        db.session.commit()

        # Resolve market to YES
        self.market.resolve(True)
        self.market.award_xp_for_predictions()

        user = User.query.get(self.user1.id)
        # Verify XP was awarded (should be 10 * shares)
        self.assertGreater(user.xp, 0)
        self.assertTrue(self.prediction.xp_awarded)

    def test_incorrect_prediction_awards_no_xp(self):
        """Test that incorrect predictions do not award XP"""
        # Make an incorrect prediction
        self.prediction.outcome = False
        db.session.commit()

        # Resolve market to YES
        self.market.resolve(True)
        self.market.award_xp_for_predictions()

        user = User.query.get(self.user1.id)
        # Verify no XP was awarded
        self.assertEqual(user.xp, 0)
        self.assertTrue(self.prediction.xp_awarded)

    def test_xp_not_awarded_twice(self):
        """Test that XP is not awarded twice for the same prediction"""
        # Make a correct prediction
        self.prediction.outcome = True
        db.session.commit()

        # Resolve market to YES
        self.market.resolve(True)
        self.market.award_xp_for_predictions()
        
        # Save XP before second award attempt
        initial_xp = self.user1.xp
        
        # Try to award XP again
        self.market.award_xp_for_predictions()
        
        # Verify XP did not change (since prediction was already marked as awarded)
        self.assertEqual(self.user1.xp, initial_xp)

    def test_multiple_predictions_with_mixed_outcomes(self):
        """Test XP awarding with multiple predictions with mixed outcomes"""
        # Create second prediction for same user
        prediction2 = Prediction(
            user_id=self.user1.id,
            market_id=self.market.id,
            outcome=False,
            shares=15
        )
        db.session.add(prediction2)
        db.session.commit()
        
        # Resolve market with YES outcome
        self.market.resolve(True)
        self.market.award_xp_for_predictions()
        
        # Verify XP is awarded only for correct prediction
        user = User.query.get(self.user1.id)
        self.assertGreater(user.xp, 0)  # Should have XP from correct prediction
        
    def test_no_predictions_on_resolved_market(self):
        """Test that resolving a market with no predictions doesn't affect XP"""
        # Create new market without predictions
        market = Market(
            title="Test Market",
            description="No predictions market",
            resolution_date=datetime.utcnow() + timedelta(days=1),
            resolution_method="manual",
            domain="test",
            yes_pool=1000.0,
            no_pool=1000.0,
            liquidity_pool=2000.0,
            liquidity_provider_shares=1.0,
            liquidity_fee=0.003
        )
        db.session.add(market)
        db.session.commit()
        
        # Resolve market
        market.resolve(True)
        market.award_xp_for_predictions()
        
        # Verify user XP remains unchanged
        user = User.query.get(self.user1.id)
        self.assertEqual(user.xp, 0)  # No predictions, no XP change

    def test_incorrect_prediction_awards_no_xp(self):
        """Test that incorrect predictions award 0 XP"""
        # Update prediction to be incorrect
        self.prediction.outcome = False
        db.session.commit()
        
        # Resolve market with opposite outcome
        self.market.resolve(True)
        db.session.commit()
        
        # Award XP for predictions
        self.market.award_xp_for_predictions()
        db.session.commit()
        
        # Verify user received no XP
        user = User.query.get(self.user1.id)
        self.assertEqual(user.xp, 0)
