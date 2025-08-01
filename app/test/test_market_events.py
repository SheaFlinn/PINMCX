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

            deadline=datetime.utcnow() + timedelta(days=1),
            creator_id=self.user.id,
            platform_fee=0.05,
            liquidity_fee=0.01,
            status='open'
        )
        db.session.add(self.market)
        db.session.commit()
        
        # Log market creation event using the proper method
        MarketEvent.log_market_creation(self.market, self.user.id)

            resolution_date=datetime.utcnow() + timedelta(days=1),
            resolution_method='Test method'
        )
        db.session.add(self.market)
        db.session.commit()
 231818b (✅ All XP prediction tests passing)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_market_creation_event(self):
        """Test that market creation logs an event"""
        # Create a new market
        market = Market(
            title='New Test Market',
            description='Created for testing events',

            deadline=datetime.utcnow() + timedelta(days=1),
            creator_id=self.user.id,
            platform_fee=0.05,
            liquidity_fee=0.01,
            status='open'

            resolution_date=datetime.utcnow() + timedelta(days=1),
            resolution_method='Test method'
 231818b (✅ All XP prediction tests passing)
        )
        db.session.add(market)
        db.session.commit()
        

        # Log market creation event using the proper method
        MarketEvent.log_market_creation(market, self.user.id)
        db.session.commit()
        

 231818b (✅ All XP prediction tests passing)
        # Verify event was created
        event = MarketEvent.query.filter_by(
            market_id=market.id,
            event_type='market_created'
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.description, f'Market "{market.title}" created')
        self.assertIsNotNone(event.event_data)
        
        # Verify event data contains essential fields
        self.assertIn('title', event.event_data)
        self.assertIn('description', event.event_data)

        self.assertIn('deadline', event.event_data)
        self.assertIn('platform_fee', event.event_data)
        self.assertIn('liquidity_fee', event.event_data)

        self.assertIn('resolution_date', event.event_data)
 231818b (✅ All XP prediction tests passing)

    def test_market_resolution_event(self):
        """Test that market resolution logs an event"""
        # Create a prediction for the market
        prediction = Prediction(

            user_id=self.user.id,
            market_id=self.market.id,
            outcome='YES',
            stake=10.0,
            confidence=1.0,
            timestamp=datetime.utcnow()

            market_id=self.market.id,
            user_id=self.user.id,
            prediction='YES',
            shares=10
 231818b (✅ All XP prediction tests passing)
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

        self.assertEqual(event.description, f'Market "{self.market.title}" resolved to YES')

        self.assertEqual(event.description, f'Market "{self.market.title}" resolved')
 231818b (✅ All XP prediction tests passing)
        self.assertIsNotNone(event.event_data)
        
        # Verify event data contains resolution details
        self.assertIn('outcome', event.event_data)
        self.assertIn('resolved_at', event.event_data)
        self.assertIn('lineage', event.event_data)

    def test_prediction_event(self):
        """Test that predictions log events"""
        # Create a prediction
        prediction = Prediction(

            user_id=self.user.id,
            market_id=self.market.id,
            outcome='YES',
            stake=10.0,
            confidence=1.0,
            timestamp=datetime.utcnow()

            market_id=self.market.id,
            user_id=self.user.id,
            prediction='YES',
            shares=10
 231818b (✅ All XP prediction tests passing)
        )
        db.session.add(prediction)
        db.session.commit()
        
        # Verify prediction event was created
        event = MarketEvent.query.filter_by(
            market_id=self.market.id,

            user_id=self.user.id,
            event_type='prediction_created'
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.description, f'Prediction created for market "{self.market.title}"')
        self.assertIsNotNone(event.event_data)
        
        # Verify event data contains prediction details
        self.assertIn('outcome', event.event_data)
        self.assertIn('stake', event.event_data)
        self.assertIn('confidence', event.event_data)

            event_type='prediction_made'
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.description, f'Prediction made on market "{self.market.title}"')
        self.assertIsNotNone(event.event_data)
        
        # Verify event data contains prediction details
        self.assertIn('user_id', event.event_data)
        self.assertIn('prediction', event.event_data)
        self.assertIn('shares', event.event_data)
 231818b (✅ All XP prediction tests passing)

if __name__ == '__main__':
    unittest.main()
