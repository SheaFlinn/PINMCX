import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import AMMMarket, PublishedContract

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def test_contract(app):
    """Create and save a test PublishedContract instance to the database."""
    with app.app_context():
        contract = PublishedContract(
            city="Test City",
            title="Test Contract",
            description="Test description",
            resolution_method="Test resolution method",
            source_url="http://test.com",
            resolution_date=datetime.utcnow() + timedelta(days=90)
        )
        with db.session.begin():
            db.session.add(contract)
            db.session.commit()
        return db.session.merge(contract)  # Ensure contract is bound to session

@pytest.fixture
def test_market(app, test_contract):
    """Create and save a test AMMMarket instance associated with test_contract."""
    with app.app_context():
        market = AMMMarket(
            contract=test_contract,
            base_pool=1000.0,
            quote_pool=1000.0
        )
        with db.session.begin():
            db.session.add(market)
            db.session.commit()
        return db.session.merge(market)  # Ensure market is bound to session

@pytest.fixture
def saved_market(app, test_contract, test_market):
    """Create and save a test market and contract to the database."""
    with app.app_context():
        # Force load the relationship while still in session
        db.session.refresh(test_market)
        db.session.refresh(test_contract)
        return test_market

def test_market_relationship(app, test_contract, test_market):
    """Test that AMMMarket.contract relationship loads the correct PublishedContract."""
    with app.app_context():
        # Ensure objects are bound to session
        market = db.session.merge(test_market)
        contract = db.session.merge(test_contract)
        assert market.contract is not None
        assert market.contract.title == "Test Contract"
        assert market.contract.city == "Test City"

def test_market_defaults(app, test_contract, test_market):
    """Test that AMMMarket has correct default values on creation."""
    with app.app_context():
        # Ensure objects are bound to session
        market = db.session.merge(test_market)
        contract = db.session.merge(test_contract)
        
        assert market.base_pool == 1000.0
        assert market.quote_pool == 1000.0
        assert market.total_shares_yes == 0.0
        assert market.total_shares_no == 0.0
        assert market.created_at is not None
        assert market.updated_at is not None
        assert isinstance(market.created_at, datetime)
        assert isinstance(market.updated_at, datetime)
