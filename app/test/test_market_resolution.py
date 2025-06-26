import pytest
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models import User, Market, Prediction

@pytest.fixture
def test_app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def sample_user():
    user = User(username="user1", email="user1@example.com")
    user.set_password("password")
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def unresolved_market(sample_user):
    market = Market(
        title="Will it rain tomorrow?",
        description="Test resolution",
        resolution_date=datetime.utcnow(),
        resolution_method="API",
        yes_pool=1000,
        no_pool=1000,
        refined_by=sample_user.id
    )
    db.session.add(market)
    db.session.commit()
    return market

def test_resolve_market_yes(test_app, sample_user, unresolved_market):
    market = unresolved_market

    # Add prediction
    prediction = Prediction(
        user_id=sample_user.id,
        market_id=market.id,
        outcome='YES',
        amount=100,
        shares=10
    )
    db.session.add(prediction)
    db.session.commit()

    # Resolve market
    market.resolve('YES')
    db.session.commit()

    assert market.resolved is True
    assert market.resolved_outcome == 'YES'
    assert prediction.payout > 0
    assert sample_user.points > 0

def test_resolve_market_invalid_outcome(test_app, unresolved_market):
    market = unresolved_market

    with pytest.raises(ValueError):
        market.resolve('MAYBE')
