import unittest
from app import create_app, db
from app.models import User, Market, Prediction, MarketEvent
from datetime import datetime, timedelta

class TestMarketEvents(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Register models with the test app
        import app.models
        db.create_all()
        
        # Create test user
        self.user = User(username='test', email='test@example.com')
        db.session.add(self.user)
        db.session.commit()
        
        # Create test market
        self.market = Market(
            title='Test Market',
            description='Test market for events',
            resolution_date=datetime.utcnow() + timedelta(days=1),
            resolution_method='Test method'
        )
        db.session.add(self.market)
        db.session.commit()
        # Log market creation event
        event = MarketEvent.log_market_creation(self.market, user_id=self.user.id)
        db.session.add(event)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_market_creation_event(self):
        """Test that market creation logs an event"""
        # Create a new market using the new method
        market, event = Market.create_with_event(
            title='New Test Market',
            description='Created for testing events',
            resolution_date=datetime.utcnow() + timedelta(days=1),
            resolution_method='Test method'
        )
        
        # Verify event was created
        self.assertIsNotNone(event)
        self.assertEqual(event.description, f'Market "{market.title}" created')
        self.assertIsNotNone(event.event_data)
        
        # Verify event data contains essential fields
        self.assertIn('title', event.event_data)
        self.assertIn('description', event.event_data)
        self.assertIn('resolution_date', event.event_data)

    def test_market_resolution_event(self):
        """Test that market resolution logs an event"""
        # Create a prediction for the market
        prediction = Prediction(
            market_id=self.market.id,
            user_id=self.user.id,
            outcome=True,
            shares=10
        )
        db.session.add(prediction)
        db.session.commit()
        
        # Resolve the market
        self.market.resolve('YES')
        db.session.commit()
        
        # Verify resolution event was created
        event = MarketEvent.query.filter_by(
            market_id=self.market.id,
            event_type='market_resolved'
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.description, f'Market "{self.market.title}" resolved')
        self.assertIsNotNone(event.event_data)
        
        # Verify event data contains resolution details
        self.assertIn('outcome', event.event_data)
        self.assertIn('resolved_at', event.event_data)
        self.assertIn('lineage', event.event_data)

    def test_prediction_event(self):
        """Test that predictions log events"""
        # Create a prediction
        prediction = Prediction(
            market_id=self.market.id,
            user_id=self.user.id,
            outcome=True,
            shares=10
        )
        db.session.add(prediction)
        db.session.commit()
        
        # Verify prediction event was created
        event = MarketEvent.query.filter_by(
            market_id=self.market.id,
            event_type='prediction'
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.description, f"Prediction made by user {self.user.id} on market {self.market.id}")
        self.assertIsNotNone(event.event_data)
        
        # Verify event data contains prediction details
        self.assertIn('prediction_id', event.event_data)
        self.assertIn('shares', event.event_data)
        self.assertIn('outcome', event.event_data)
        self.assertIn('xp_awarded', event.event_data)

if __name__ == '__main__':
    unittest.main()
