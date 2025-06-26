import unittest
from datetime import datetime, timedelta
from app import create_app, db

from app.models import User, Market, Prediction, Badge, MarketEvent

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

        MarketEvent  # Force import of MarketEvent model

 231818b (✅ All XP prediction tests passing)

        # Create test users
        self.user1 = User(username='test1', email='test1@example.com')
        self.user2 = User(username='test2', email='test2@example.com')
        db.session.add_all([self.user1, self.user2])
        db.session.commit()

        # Create test market
        self.market = Market(
            title="Will it rain tomorrow?",
            description="A test market for rain prediction",

            deadline=datetime.utcnow() + timedelta(days=1),
            creator_id=self.user1.id,
            platform_fee=0.05,
            liquidity_fee=0.01,
            status='open'

            resolution_date=datetime.utcnow() + timedelta(days=1),
            resolution_method="manual",
            domain="weather",
            yes_pool=1000.0,
            no_pool=1000.0,
            liquidity_pool=2000.0,
            liquidity_provider_shares=1.0,
            liquidity_fee=0.003
 231818b (✅ All XP prediction tests passing)
        )
        db.session.add(self.market)
        db.session.commit()

        # Create test prediction
        self.prediction = Prediction(
            user_id=self.user1.id,
            market_id=self.market.id,

            outcome='YES',
            confidence=1.0,
            stake=10.0,
            timestamp=datetime.utcnow()

            prediction="YES",
            shares=10,
            average_price=0.5
 231818b (✅ All XP prediction tests passing)
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
        self.prediction.outcome = 'YES'
        db.session.commit()

        # Resolve market to YES
        self.market.resolve('YES')
        self.market.award_xp_for_predictions()

        user = User.query.get(self.user1.id)
        # Verify XP was awarded (should be 10 * stake)
        self.assertGreater(user.xp, 0)
        self.assertTrue(self.prediction.xp_awarded)

    def test_incorrect_prediction_awards_no_xp(self):
        """Test that incorrect predictions do not award XP"""
        # Make an incorrect prediction
        self.prediction.outcome = 'NO'
        db.session.commit()

        # Resolve market to YES
        self.market.resolve('YES')
        self.market.award_xp_for_predictions()

        user = User.query.get(self.user1.id)
        # Verify no XP was awarded
        self.assertEqual(user.xp, 0)
        self.assertTrue(self.prediction.xp_awarded)

    def test_xp_not_awarded_twice(self):
        """Test that XP is not awarded twice for the same prediction"""
        # Make a correct prediction
        self.prediction.outcome = 'YES'
        db.session.commit()

        # Resolve market to YES
        self.market.resolve('YES')
        self.market.award_xp_for_predictions()
        
        # Save XP before second award attempt
        initial_xp = self.user1.xp
        
        # Try to award XP again
        self.market.award_xp_for_predictions()
        
        # Verify XP remains unchanged
        self.assertEqual(self.user1.xp, initial_xp)

    def test_multiple_predictions(self):
        """Test XP awarding for multiple predictions"""
        # Create second prediction
        prediction2 = Prediction(
            user_id=self.user2.id,
            market_id=self.market.id,
            outcome='YES',
            confidence=1.0,
            stake=15.0,
            timestamp=datetime.utcnow()
        )
        db.session.add(prediction2)
        db.session.commit()

        # Resolve market to YES
        self.market.resolve('YES')
        self.market.award_xp_for_predictions()

        # Verify both users received XP
        user1 = User.query.get(self.user1.id)
        user2 = User.query.get(self.user2.id)
        self.assertGreater(user1.xp, 0)
        self.assertGreater(user2.xp, 0)
        self.assertEqual(user2.xp, user1.xp * 1.5)  # user2 should have 1.5x XP due to higher stake

    def test_no_xp_for_incorrect_predictions(self):
        """Test that incorrect predictions don't affect XP"""
        # Create incorrect prediction
        prediction2 = Prediction(
            user_id=self.user2.id,
            market_id=self.market.id,
            outcome='NO',
            confidence=1.0,
            stake=15.0,
            timestamp=datetime.utcnow()
        )
        db.session.add(prediction2)
        db.session.commit()

        # Resolve market to YES
        self.market.resolve('YES')
        self.market.award_xp_for_predictions()

        # Verify only correct prediction received XP
        user1 = User.query.get(self.user1.id)
        user2 = User.query.get(self.user2.id)
        self.assertGreater(user1.xp, 0)
        self.assertEqual(user2.xp, 0)

    def test_market_resolution_event(self):
        """Test that market resolution creates proper event"""
        # Resolve the market
        self.market.resolve('YES')
        
        # Get the resolution event
        event = MarketEvent.query.filter_by(
            market_id=self.market.id,
            event_type='market_resolved'
        ).order_by(MarketEvent.created_at.desc()).first()
        
        self.assertIsNotNone(event)
        self.assertEqual(event.description, f'Market "{self.market.title}" resolved to YES')
        self.assertEqual(event.event_data['outcome'], 'YES')

if __name__ == '__main__':
    unittest.main()

        # Update prediction to be correct
        self.prediction.prediction = "YES"
        db.session.commit()
        
        # Resolve market with correct outcome
        self.market.resolve("YES")
        db.session.commit()
        
        # Award XP for predictions
        self.market.award_xp_for_predictions()
        db.session.commit()
        
        # Verify user received XP
        user = User.query.get(self.user1.id)
        self.assertGreater(user.xp, 0)
        
    def test_incorrect_prediction_awards_no_xp(self):
        """Test that incorrect predictions award 0 XP"""
        # Update prediction to be incorrect
        self.prediction.prediction = "NO"
        db.session.commit()
        
        # Resolve market with opposite outcome
        self.market.resolve("YES")
        db.session.commit()
        
        # Award XP for predictions
        self.market.award_xp_for_predictions()
        db.session.commit()
        
        # Verify user received no XP
        user = User.query.get(self.user1.id)
        self.assertEqual(user.xp, 0)
        
    def test_multiple_predictions_with_mixed_outcomes(self):
        """Test XP awarding with multiple predictions with mixed outcomes"""
        # Create second prediction for same user
        prediction2 = Prediction(
            user_id=self.user1.id,
            market_id=self.market.id,
            prediction="NO",
            shares=15,
            average_price=0.4
        )
        db.session.add(prediction2)
        db.session.commit()
        
        # Resolve market with YES outcome
        self.market.resolve("YES")
        db.session.commit()
        
        # Award XP for predictions
        self.market.award_xp_for_predictions()
        db.session.commit()
        
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
        market.resolve("YES")
        db.session.commit()
        
        # Award XP for predictions
        market.award_xp_for_predictions()
        db.session.commit()
        
        # Verify user XP remains unchanged
        user = User.query.get(self.user1.id)
        self.assertEqual(user.xp, 0)  # No predictions, no XP change

    def test_incorrect_prediction_awards_no_xp(self):
        """Test that incorrect predictions award 0 XP"""
        # Update prediction to be incorrect
        self.prediction.prediction = "NO"
        db.session.commit()
        
        # Resolve market with opposite outcome
        self.market.resolve("YES")
        db.session.commit()
        
        # Award XP for predictions
        self.market.award_xp_for_predictions()
        db.session.commit()
        
        # Verify user received no XP
        user = User.query.get(self.user1.id)
        self.assertEqual(user.xp, 0)
 231818b (✅ All XP prediction tests passing)
