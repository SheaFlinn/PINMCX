import pytest
from app import create_app, db
from app.models import user, market, prediction, market_event, platform_wallet, news, liquidity_pool, liquidity_provider, user_ledger, amm_market

@pytest.fixture(scope="function")
def app():
    """Create and configure a new app instance for each test."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'connect_args': {'timeout': 15}
        }
    })
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Register models
        models = [
            user.User,
            market.Market,
            prediction.Prediction,
            market_event.MarketEvent,
            platform_wallet.PlatformWallet,
            news.NewsSource,
            news.NewsHeadline,
            liquidity_pool.LiquidityPool,
            liquidity_provider.LiquidityProvider,
            user_ledger.UserLedger,
            amm_market.AMMMarket
        ]
        print(f"Registered tables after init_app: {dict([(model.__tablename__, model.__tablename__) for model in models])}")
        
    yield app
    
    # Cleanup
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_app():
    """Create and configure a new app instance for each test."""
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'connect_args': {'timeout': 15}
        }
    }
    
    app = create_app(test_config)
    
    with app.app_context():
        db.create_all()
        
        # Register models
        models = [
            user.User,
            market.Market,
            prediction.Prediction,
            market_event.MarketEvent,
            platform_wallet.PlatformWallet,
            news.NewsSource,
            news.NewsHeadline,
            liquidity_pool.LiquidityPool,
            liquidity_provider.LiquidityProvider,
            user_ledger.UserLedger,
            amm_market.AMMMarket
        ]
        print(f"Registered tables after init_app: {dict([(model.__tablename__, model.__tablename__) for model in models])}")
        
    yield app
    
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_client(test_app):
    """Provide a test client for the app."""
    return test_app.test_client()

@pytest.fixture
def test_db(test_app):
    """Provide a clean database for tests."""
    with test_app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_user(test_app, test_db):
    """Fixture for a test user with points and liquidity buffer."""
    with test_app.app_context():
        user = user.User(
            username="testuser",
            email="test@example.com"
        )
        test_db.session.add(user)
        test_db.session.commit()
        
        # Update user after commit
        user = test_db.session.get(user.User, user.id)
        user.points = 1000
        user.liquidity_buffer_deposit = 500
        user.predictions_count = 0
        
        test_db.session.commit()
        
        yield user
        
        # Cleanup
        test_db.session.delete(user)
        test_db.session.commit()

@pytest.fixture
def test_market(test_app, test_db, test_user):
    """Fixture for a test market with valid attributes."""
    with test_app.app_context():
        market = market.Market(
            title="Test Market",
            description="Test market description",
            resolution_date=datetime.utcnow() + timedelta(days=90),
            resolution_method="Test resolution method",
            prediction_deadline=datetime.utcnow() + timedelta(days=89),
            resolution_deadline=datetime.utcnow() + timedelta(days=90)
        )
        
        # Initialize pools
        market.yes_pool = 1000.0
        market.no_pool = 1000.0
        market.liquidity_pool = 2000.0
        
        # Create and associate a LiquidityPool instance
        liquidity_pool = liquidity_pool.LiquidityPool(
            contract_id=market.id,
            max_liquidity=2000,
            current_liquidity=2000
        )
        market.market_liquidity_pool = liquidity_pool
        
        market.liquidity_provider_shares = 1.0
        market.liquidity_fee = 0.003
        
        # Initialize relationships with empty lists
        market.predictions = []
        market.events = []
        market.liquidity_providers = []
        market.child_markets = []
        market.parent_market = None
        
        # Add market and liquidity pool to session
        test_db.session.add(market)
        test_db.session.add(liquidity_pool)
        
        # Commit everything together
        test_db.session.commit()
        
        # Refresh market after commit
        market = test_db.session.get(market.Market, market.id)
        
        yield market
        
        # Cleanup
        test_db.session.delete(market)
        test_db.session.delete(liquidity_pool)
        test_db.session.commit()

@pytest.fixture
def test_prediction(test_app, test_db, test_user, test_market):
    """Fixture for a test prediction."""
    with test_app.app_context():
        prediction = prediction.Prediction(
            user_id=test_user.id,
            market_id=test_market.id,
            stake=100,
            outcome="YES",
            shares_purchased=0.5,
            price=1.0
        )
        
        # Set relationships
        prediction.user = test_user
        prediction.market = test_market
        
        test_db.session.add(prediction)
        test_db.session.commit()
        
        # Refresh prediction after commit
        prediction = test_db.session.get(prediction.Prediction, prediction.id)
        
        yield prediction
        
        # Cleanup
        test_db.session.delete(prediction)
        test_db.session.commit()
